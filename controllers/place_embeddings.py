from typing import List, Tuple
from controllers.embeddings import GeminiEmbeddingsAPI
from controllers.places import GooglePlacesAPI 
from db.tidb_vector_store import TiDBVectorStore
from utils.logger import get_logger
import json
logger = get_logger(__name__)

def convert_places_to_embeddings(places_data: List[dict], api_keys=None) -> List[Tuple[List[float], str]]:
    """Convert places API results to embeddings using multithreading."""
    if not places_data:
        return []
    
    embeddings_api = GeminiEmbeddingsAPI(user_api_keys=api_keys)
    vector_store = TiDBVectorStore()
    
    # Prepare text data and place IDs
    texts_and_ids = []
    place_ids = []
    id_to_name_map = {}
    
    for place in places_data:
        try:
            place_id = place.get('place_id', '')
            name = place.get('displayName', {}).get('text', '')
            primary_type = place.get('primaryType', '')
            types = ', '.join(place.get('types', []))
            
            # Get review texts
            reviews = []
            for review in place.get('reviews', []):
                text = review.get('text', {}).get('text', '')
                if text:
                    reviews.append(text)
            reviews_text = ' '.join(reviews)
            
            # Combine all text
            combined_text = f"{name} {primary_type} {types} {reviews_text}".strip()
            texts_and_ids.append((combined_text, place_id, name))
            place_ids.append(place_id)
            id_to_name_map[place_id] = name
            
        except Exception as e:
            logger.error(f"Error processing place data: {e}")
    
    if not texts_and_ids:
        logger.warning("No valid place data to process")
        return []
    
    # Check which embeddings already exist in the database
    existing_embeddings = []
    existing_place_ids = set()
    try:
        existing_data = vector_store.search_embeddings_by_ids(place_ids)
        existing_embeddings = [(embedding, place_id) for place_id, embedding in existing_data]
        existing_place_ids = {place_id for place_id, _ in existing_data}
        
        # Calculate missing place_ids
        missing_place_ids = set(place_ids) - existing_place_ids
        logger.info(f"Found {len(existing_place_ids)} existing embeddings, {len(missing_place_ids)} missing out of {len(place_ids)} total")
        
        if missing_place_ids:
            missing_names = [id_to_name_map.get(pid, "Unknown") for pid in list(missing_place_ids)[:5]]
            missing_info = ", ".join(missing_names)
            if len(missing_place_ids) > 5:
                missing_info += f" and {len(missing_place_ids) - 5} more"
            logger.info(f"Missing embeddings for: {missing_info}")
    except Exception as e:
        logger.error(f"Error checking existing embeddings: {e}")
    
    # Filter out places that already have embeddings
    new_texts_and_ids = [(text, place_id, name) for text, place_id, name in texts_and_ids 
                        if place_id not in existing_place_ids]
    
    # Generate embeddings only for new places
    new_embeddings = []
    missing_count = len(new_texts_and_ids)
    if new_texts_and_ids:
        logger.info(f"Need to generate embeddings for {missing_count} places: " + 
                   ", ".join([f"'{name}' ({place_id})" for _, place_id, name in new_texts_and_ids[:5]]) + 
                   (f" and {missing_count - 5} more" if missing_count > 5 else ""))
        
        # Extract texts for batch processing
        texts = [item[0] for item in new_texts_and_ids]
        
        # Generate embeddings in batch
        logger.info(f"Generating embeddings for {len(texts)} new places...")
        embeddings = embeddings_api.generate_embeddings_batch(texts)
        
        # Check if any embeddings were generated
        if not any(embeddings):
            logger.error("Failed to generate any embeddings. Check API keys or rate limits.")
        
        # Combine results
        for i, (text, place_id, name) in enumerate(new_texts_and_ids):
            embedding = embeddings[i]
            if embedding:
                new_embeddings.append((embedding, place_id))
                logger.debug(f"Generated embedding for place: {name} (ID: {place_id})")
            else:
                logger.warning(f"Failed to generate embedding for place: {name} (ID: {place_id})")
        
        # Store new embeddings in the database
        if new_embeddings:
            try:
                stored, failed = vector_store.store_embeddings(new_embeddings)
                logger.info(f"Stored {stored} new embeddings in database, {failed} failed")
            except Exception as e:
                logger.error(f"Error storing new embeddings: {e}")
    else:
        logger.info("No new embeddings needed - all places already have embeddings in the database")
    
    # Combine existing and new embeddings
    results = existing_embeddings + new_embeddings
    
    new_count = len(new_embeddings)
    existing_count = len(existing_embeddings)
    total_count = len(results)
    missing = len(place_ids) - total_count
    logger.info(f"Used {existing_count} existing and generated {new_count} new embeddings. Total: {total_count}/{len(places_data)} places")
    
    if missing > 0:
        logger.warning(f"Missing embeddings for {missing} places after processing")
    
    return results

def find_nearest_embeddings(target_embedding: List[float], limit: int = 10, filter_place_ids: List[str] = None, api_keys=None) -> List[str]:
    """Find the nearest embeddings to a target embedding using TiDB vector similarity search."""
    vector_store = TiDBVectorStore()
    connection = vector_store.get_connection()
    cursor = connection.cursor()
    
    try:
        # Convert embedding to TiDB VECTOR format
        embedding_str = '[' + ','.join(map(str, target_embedding)) + ']'
        
        # Build query with optional filtering
        if filter_place_ids and len(filter_place_ids) > 0:
            # Create placeholders for IN clause
            placeholders = ','.join(['%s'] * len(filter_place_ids))
            query = f"""
            SELECT place_id, VEC_COSINE_DISTANCE(embedding, %s) as distance
            FROM {vector_store.table_name}
            WHERE place_id IN ({placeholders})
            ORDER BY distance ASC
            LIMIT %s
            """
            params = [embedding_str] + filter_place_ids + [limit]
        else:
            # Search all embeddings
            query = f"""
            SELECT place_id, VEC_COSINE_DISTANCE(embedding, %s) as distance
            FROM {vector_store.table_name}
            ORDER BY distance ASC
            LIMIT %s
            """
            params = [embedding_str, limit]
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        # Extract just the place_ids
        place_ids = [row[0] for row in results]
        
        filter_info = f" (filtered to {len(filter_place_ids)} candidates)" if filter_place_ids else ""
        logger.info(f"Found {len(place_ids)} nearest embeddings{filter_info}")
        return place_ids
        
    except Exception as e:
        logger.error(f"Error finding nearest embeddings: {e}")
        return []
    finally:
        cursor.close()
        connection.close()


def main():
    query = "coffee shops in Gurugram"
    API=GooglePlacesAPI()
    # Call the search method
    results = API.search_places_with_details(query=query)
    if results:
        print(f"✅ Found {len(results)} places for query: '{query}'")
        for i, place in enumerate(results[:5], start=1):  # Show first 5 results
            print(f"\n=== Result {i} ===")
            print(json.dumps(place, indent=2))  # Pretty print full JSON
    else:
        print("⚠️ No results found or error occurred.")
    embeddings=convert_places_to_embeddings(results)
    if embeddings:
        print("\n=== Embeddings Output ===")
        for embedding, place_id in embeddings:
            print(f"\nPlace ID: {place_id}")
            print(f"Embedding length: {len(embedding)}")
            print(f"First 10 dims: {embedding[:10]} ...")  # just preview
    else:
        print("⚠️ No embeddings done")

if __name__=="__main__":
    main()