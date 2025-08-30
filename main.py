import json 
import re
from typing import Dict, List, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from controllers.llm_calls import GeminiLLM
from controllers.places import GooglePlacesAPI
from controllers.embeddings import GeminiEmbeddingsAPI
from db.place_embeddings_store import store_places_to_tidb
from utils.logger import get_logger
from utils.config import Config

logger = get_logger(__name__)

def llm_vendor_type(user_event_description):
    """
    Analyze event description and return required vendor categories in JSON format
    """

    prompt = f"""You are an expert Event Planner. 
    Your task is to analyze the given event description and generate a comprehensive JSON list of vendor categories required for the successful execution of that event. 

    Rules:
    - Always return output STRICTLY in JSON.
    - The JSON must include "event_type" and a "vendors" array.
    - The "vendors" array should list all vendor categories relevant to the event.
    - Think broadly and include both common and uncommon vendors depending on the event requirements.

    User Input:
    "{user_event_description}"
    """
    
    try:
        logger.info("Figuring Out vendor types...")
        llm = GeminiLLM()
        response = llm.generate(prompt, temperature=0.7)

        match = re.search(r"\{.*\}", response, re.DOTALL)
        if not match:
            raise GeminiLLMError("No valid JSON found in LLM response")

        json_str = match.group(0).strip()

        # Parse into dict
        parsed_json = json.loads(json_str)

        return parsed_json
        
    except Exception as e:
        logger.error(f"Error analyzing vendor types: {e}")
        return None

def generate_vendor_search_queries(vendor_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Takes vendor categories and generates Google Places API–friendly search queries
    """
    vendors = vendor_data.get("vendors")

    prompt = f"""You are an expert event planning consultant with extensive experience of using Google Maps to find vendors.
    Given the following vendor categories for an event, generate optimized Google Maps/Places search queries.
    
    Rules:
    - Make queries specific and realistic for Google Places API/ Google Maps.
    - Keep them short
    - Return STRICTLY in JSON array format like:
      [
        {{"vendor_type": "...", "query": "..."}},
        ...
      ]
    
    Vendors: {vendors}
    """

    try:
        llm = GeminiLLM()
        logger.info("Generating vendor search queries...")
        response = llm.generate(prompt, temperature=0.5)

        match = re.search(r"\[.*\]", response, re.DOTALL)
        if not match:
            raise ValueError("No valid JSON array found in LLM response")
            
        json_str = match.group(0).strip()
        parsed_json = json.loads(json_str)

        return parsed_json

    except Exception as e:
        logger.error(f"Error generating vendor search queries: {e}")
        return None

def places_api_call(search_queries: List[Dict[str, Any]], location: str = None) -> List[Dict[str, Any]]:
    """Returns a list of place details for all queries using multithreading."""
    if not search_queries:
        logger.warning("No search queries provided")
        return []
    
    places_api = GooglePlacesAPI()
    logger.info(f"Places API called on {len(search_queries)} queries using multithreading")

    try:
        # Fetch location bounds if location provided
        location_bias = None
        if location:
            location_bias = places_api.get_location_bounds(location)
            if not location_bias:
                logger.error(f"Could not fetch bounds for '{location}'")
                return []
        else:
            logger.info("No location provided")
            return []

        # Wrap in Google API expected format
        location_bias = {"rectangle": location_bias}

        all_results = []
        
        def search_single_query(query_item: Dict[str, Any]) -> List[Dict[str, Any]]:
            """Search for places for a single query"""
            vendor_type = query_item.get("vendor_type")
            query = query_item.get("query")

            if not query:
                logger.warning(f"Empty query for vendor type: {vendor_type}")
                return []

            try:
                logger.info(f"Searching for {vendor_type}: {query}")
                places = places_api.search_places_with_details(query, location_bias)

                # Add context info
                for place in places:
                    place["vendor_type"] = vendor_type
                    place["search_query"] = query

                return places

            except Exception as e:
                logger.error(f"Error searching for vendor type '{vendor_type}' with query '{query}': {e}")
                return []

        # Use ThreadPoolExecutor for concurrent place searches
        
        with ThreadPoolExecutor(max_workers=3) as executor:
            # Submit all search tasks
            future_to_query = {
                executor.submit(search_single_query, query_item): query_item 
                for query_item in search_queries
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_query):
                try:
                    places = future.result()
                    all_results.extend(places)
                except Exception as e:
                    query_item = future_to_query[future]
                    logger.error(f"Error processing query {query_item.get('vendor_type', 'unknown')}: {e}")

        logger.info(f"Found {len(all_results)} total places across all queries")
        return all_results

    except Exception as e:
        logger.error(f"places_api_call failed: {e}", exc_info=True)
        return []

def semantic_match(user_event_description, places_data: List[Dict[str, Any]], limit: int = 10) -> Dict[str, List[str]]:
    """
    User input + vendor combination vector match/ranking
    """
    try:
        # Generate embedding for user input
        embedding_api = GeminiEmbeddingsAPI()
        user_input_embedding = embedding_api.generate_embedding(user_event_description)
        if not user_input_embedding:
            logger.error("Failed to generate embedding for user input")
            return {}
        
        # Group places by vendor_type
        vendor_groups = {}
        for place in places_data:
            vendor_type = place.get("vendor_type")
            place_id = place.get("place_id")
            
            if vendor_type and place_id:
                if vendor_type not in vendor_groups:
                    vendor_groups[vendor_type] = []
                vendor_groups[vendor_type].append(place_id)
        
        logger.info(f"Found {len(vendor_groups)} vendor types with places")
        
        # Import the function here to avoid circular imports
        from controllers.place_embeddings import find_nearest_embeddings
        from db.tidb_vector_store import TiDBVectorStore
        
        # For each vendor type, find nearest embeddings
        results = {}
        
        for vendor_type, place_ids in vendor_groups.items():
            try:
                logger.info(f"Finding nearest embeddings for vendor type: {vendor_type} ({len(place_ids)} candidates)")
                
                # Search only within the specific vendor group's place_ids
                nearest_place_ids = find_nearest_embeddings(
                    user_input_embedding, 
                    limit=limit, 
                    filter_place_ids=place_ids
                )
                
                results[vendor_type] = nearest_place_ids
                
                logger.info(f"Found {len(results[vendor_type])} nearest places for {vendor_type}")
                
            except Exception as e:
                logger.error(f"Error finding nearest embeddings for vendor type '{vendor_type}': {e}")
                results[vendor_type] = []
        
        return results
        
    except Exception as e:
        logger.error(f"Error in semantic_match: {e}")
        return {}


if __name__ == "__main__":
    user_event_description = """We’re launching a new eco-friendly skincare brand in New York City.
    Budget: $15,000.
    We want a trendy but affordable venue, maybe a rooftop or loft, for about 50–70 attendees including influencers and press.
    The theme should be natural and minimalist, with lots of greenery and neutral colors.
    We’ll need catering with healthy snacks and drinks, a photographer, and a space for product displays.
    The vibe should be Instagrammable and on-brand."""
    try:
        print("🚀 Starting multithreaded event planning pipeline...")
        
        # Step 1: Analyze vendor types
        print("\n📋 Analyzing vendor types...")
        vendor_categories = llm_vendor_type(user_event_description)

        if vendor_categories:
            # Step 2: Generate search queries
            print("\n🔍 Generating search queries...")
            search_queries = generate_vendor_search_queries(vendor_categories)
            print("Search Queries JSON:", json.dumps(search_queries, indent=2))
            
            location = 'New York City, United States'
            # Call the places API with the generated queries using multithreading
            print(f"\n🏢 Searching places with multithreading...")
            places_results = places_api_call(search_queries, location)
            
            output_file = "places_results.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(places_results, f, indent=2, ensure_ascii=False)
            print(f"✅ Found {len(places_results)} places total")
            
            # Store places data in TiDB for semantic matching with multithreaded embeddings
            if places_results:
                print("\n💾 Storing places data in TiDB with multithreaded embeddings...")
                successful, failed = store_places_to_tidb(places_results)
                print(f"✅ Stored {successful} places successfully, {failed} failed")
                
                # Perform semantic matching
                print("\n🎯 Performing semantic matching...")
                semantic_results = semantic_match(user_event_description, places_results, limit=10)
                
                print("\n📊 Semantic Matching Results:")
                for vendor_type, place_ids in semantic_results.items():
                    print(f"\n{vendor_type}:")
                    for i, place_id in enumerate(place_ids, 1):
                        # Find the place name for better readability
                        place_name = "Unknown"
                        for place in places_results:
                            if place.get("place_id") == place_id:
                                place_name = place.get("displayName", {}).get("text", "Unknown")
                                break
                        print(f"  {i}. {place_name} (ID: {place_id})")
                        
                print(f"\n🎉 Pipeline completed successfully with multithreading!")

    except Exception as e:
        print(f"❌ An error occurred: {e}")
        logger.error(f"Pipeline error: {e}", exc_info=True)

