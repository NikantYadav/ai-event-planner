from typing import List, Tuple
from controllers.embeddings import GeminiEmbeddingsAPI
from controllers.places import GooglePlacesAPI 
from db.tidb_vector_store import TiDBVectorStore
from utils.logger import get_logger
import json
logger = get_logger(__name__)

def convert_places_to_embeddings(places_data: List[dict]) -> List[Tuple[List[float], str]]:
    """
    Convert places API results to embeddings.
    
    Returns: List of (embedding, place_id) tuples
    """
    embeddings_api = GeminiEmbeddingsAPI()
    results = []
    
    for place in places_data:
        try:
            # Get place_id from the data
            place_id = place.get('place_id', '')
            
            # Extract text fields
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
            
            # Generate embedding
            embedding = embeddings_api.generate_embedding(combined_text)
            if embedding:
                results.append((embedding, place_id))
                logger.info(f"Generated embedding for place: {name} (ID: {place_id})")
            else:
                logger.warning(f"Failed to generate embedding for place: {name} (ID: {place_id})")
                
        except Exception as e:
            logger.error(f"Error processing place: {e}")
    
    logger.info(f"Generated embeddings for {len(results)}/{len(places_data)} places")
    return results

def find_nearest_embeddings(target_embedding: List[float], limit: int = 10, filter_place_ids: List[str] = None) -> List[str]:
    """
    Find the nearest embeddings to a target embedding using TiDB vector similarity search.
    """
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
    if embedding:
        print("\n=== Embeddings Output ===")
    for embedding, place_id in embeddings:
        print(f"\nPlace ID: {place_id}")
        print(f"Embedding length: {len(embedding)}")
        print(f"First 10 dims: {embedding[:10]} ...")  # just preview
    else:
        print("⚠️ No embeddings done")

if __name__=="__main__":
    main()