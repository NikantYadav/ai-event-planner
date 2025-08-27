import json 
import re
from typing import Dict, List, Any
from controllers.llm_calls import GeminiLLM
from controllers.places import GooglePlacesAPI
from utils.logger import get_logger

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
    """
    Returns a list of place details for all queries.
    """
    if not search_queries:
        logger.warning("No search queries provided")
        return []
    
    places_api = GooglePlacesAPI()
    logger.info("Places API called on each query")
    all_results = []

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

        # Process each query
        for query_item in search_queries:
            vendor_type = query_item.get("vendor_type")
            query = query_item.get("query")

            if not query:
                logger.warning(f"Empty query for vendor type: {vendor_type}")
                continue

            try:
                logger.info(f"Searching for {vendor_type}: {query}")
                places = places_api.search_places_with_details(query, location_bias)

                # Add context info
                for place in places:
                    place["vendor_type"] = vendor_type
                    place["search_query"] = query

                all_results.extend(places)

            except Exception as e:
                logger.error(f"Error searching for vendor type '{vendor_type}' with query '{query}': {e}")
                continue

        logger.info(f"Found {len(all_results)} total places across all queries")
        return all_results

    except Exception as e:
        logger.error(f"places_api_call failed: {e}", exc_info=True)
        return []


if __name__ == "__main__":
    user_event_description = """We’re launching a new eco-friendly skincare brand in New York City.
    Budget: $15,000.
    We want a trendy but affordable venue, maybe a rooftop or loft, for about 50–70 attendees including influencers and press.
    The theme should be natural and minimalist, with lots of greenery and neutral colors.
    We’ll need catering with healthy snacks and drinks, a photographer, and a space for product displays.
    The vibe should be Instagrammable and on-brand."""
    try:
        vendor_categories = llm_vendor_type(user_event_description)

        if vendor_categories:
            search_queries = generate_vendor_search_queries(vendor_categories)
            print("Search Queries JSON:", json.dumps(search_queries, indent=2))
            
            location = 'New York City, United States'
            # Call the places API with the generated queries
            places_results = places_api_call(search_queries, location)
            print(f"\nFound {len(places_results)} places total")
            print("Places Results:", json.dumps(places_results, indent=20))

    except Exception as e:
        print(f"An error occurred: {e}")

