from typing import List, Tuple
from .tidb_vector_store import TiDBVectorStore
from controllers.place_embeddings import convert_places_to_embeddings
from utils.logger import get_logger

logger = get_logger(__name__)

def store_places_to_tidb(places_data: List[dict], table_name: str = "place_embeddings", api_keys=None):
    """Function to store place embeddings in TiDB using multithreaded embedding generation."""
    # Create vector store
    vector_store = TiDBVectorStore(table_name)
    
    # Create table if it doesn't exist
    vector_store.create_table()
    
    # Convert places to embeddings using multithreading
    logger.info(f"Converting {len(places_data)} places to embeddings...")
    embeddings_data = convert_places_to_embeddings(places_data, api_keys=api_keys)
    
    # Check if we have all the embeddings
    if len(embeddings_data) < len(places_data):
        logger.warning(f"Only generated {len(embeddings_data)} embeddings out of {len(places_data)} places")
    
    if not embeddings_data:
        logger.warning("No embeddings generated")
        return 0, len(places_data)
    
    # Store embeddings
    successful, failed = vector_store.store_embeddings(embeddings_data)
    
    logger.info(f"Processed {len(places_data)} places: {successful} stored, {failed} failed")
    
    # Check if any places are missing
    missing = len(places_data) - successful
    if missing > 0:
        logger.warning(f"Missing embeddings for {missing} places")
    
    return successful, failed