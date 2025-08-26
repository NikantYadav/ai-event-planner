from typing import List, Tuple
from .tidb_vector_store import TiDBVectorStore
from api.place_embeddings import convert_places_to_embeddings
from utils.logger import get_logger

logger = get_logger(__name__)

def store_places_to_tidb(places_data: List[dict], table_name: str = "place_embeddings"):
    """
    Function to store place embeddings in TiDB.
    """
    # Create vector store
    vector_store = TiDBVectorStore(table_name)
    
    # Create table if it doesn't exist
    vector_store.create_table()
    
    # Convert places to embeddings
    embeddings_data = convert_places_to_embeddings(places_data)
    
    if not embeddings_data:
        logger.warning("No embeddings generated")
        return 0, len(places_data)
    
    # Store embeddings
    successful, failed = vector_store.store_embeddings(embeddings_data)
    
    logger.info(f"Processed {len(places_data)} places: {successful} stored, {failed} failed")
    return successful, failed