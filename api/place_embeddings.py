from typing import List, Tuple
from api.embeddings import GeminiEmbeddingsAPI
from utils.logger import get_logger

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
            for review in place.get('reviews', [])[:3]:
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
                logger.info(f"Embedding: {embedding}")
            else:
                logger.warning(f"Failed to generate embedding for place: {name} (ID: {place_id})")
                
        except Exception as e:
            logger.error(f"Error processing place: {e}")
    
    logger.info(f"Generated embeddings for {len(results)}/{len(places_data)} places")
    return results