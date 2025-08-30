import mysql.connector
from typing import List, Tuple
from utils.logger import get_logger
from utils.config import Config

logger = get_logger(__name__)

class TiDBVectorStore:
    def __init__(self, table_name: str = "place_embeddings"):
        self.db_config = Config.DB_CONFIG
        self.table_name = table_name
        
    def get_connection(self):
        return mysql.connector.connect(**self.db_config)
    
    def create_table(self):
        connection = self.get_connection()
        cursor = connection.cursor()
        
        try:
            create_table_query = f"""
            CREATE TABLE IF NOT EXISTS {self.table_name} (
                place_id VARCHAR(255) PRIMARY KEY,
                embedding VECTOR(1536) NOT NULL
            )
            """
            cursor.execute(create_table_query)
            connection.commit()
            logger.info(f"Table '{self.table_name}' created")
            
        except mysql.connector.Error as err:
            logger.error(f"Error creating table: {err}")
            raise
        finally:
            cursor.close()
            connection.close()
    
    def store_embeddings(self, embeddings_data: List[Tuple[List[float], str]]):
        """Store list of (embedding, place_id) tuples"""
        connection = self.get_connection()
        cursor = connection.cursor()
        
        successful = 0
        failed = 0
        
        try:
            for embedding, place_id in embeddings_data:
                try:
                    # Convert embedding to TiDB VECTOR format
                    embedding_str = '[' + ','.join(map(str, embedding)) + ']'
                    
                    query = f"""
                    INSERT INTO {self.table_name} (place_id, embedding) 
                    VALUES (%s, %s)
                    ON DUPLICATE KEY UPDATE embedding = VALUES(embedding)
                    """
                    
                    cursor.execute(query, (place_id, embedding_str))
                    successful += 1
                    logger.info(f"Stored embedding for place_id: {place_id}")
                    
                except mysql.connector.Error as err:
                    logger.error(f"Error storing {place_id}: {err}")
                    failed += 1
            
            connection.commit()
            logger.info(f"Stored {successful} embeddings, {failed} failed")
            
        finally:
            cursor.close()
            connection.close()
            
        return successful, failed
    
    def fetch_embedding_by_id(self, place_id: str) -> Tuple[str, List[float]] | None:
        """Fetch embedding and ID for a specific place_id"""
        connection = self.get_connection()
        cursor = connection.cursor()
        
        try:
            query = f"""
            SELECT place_id, embedding 
            FROM {self.table_name} 
            WHERE place_id = %s
            """
            
            cursor.execute(query, (place_id,))
            result = cursor.fetchone()
            
            if result:
                place_id, embedding_str = result
                # Convert TiDB VECTOR format back to list of floats
                embedding_str = embedding_str.strip('[]')
                embedding = [float(x.strip()) for x in embedding_str.split(',')]
                
                logger.info(f"Retrieved embedding for place_id: {place_id}")
                return place_id, embedding
            else:
                logger.warning(f"No embedding found for place_id: {place_id}")
                return None
                
        except mysql.connector.Error as err:
            logger.error(f"Error fetching embedding for {place_id}: {err}")
            return None
        finally:
            cursor.close()
            connection.close()
    
    def search_embeddings_by_ids(self, place_ids: List[str]) -> List[Tuple[str, List[float]]]:
        """Fetch embeddings for multiple place_ids"""
        connection = self.get_connection()
        cursor = connection.cursor()
        
        results = []
        
        try:
            if not place_ids:
                logger.warning("No place_ids provided for search")
                return results
            
            # Create placeholders for IN clause
            placeholders = ','.join(['%s'] * len(place_ids))
            query = f"""
            SELECT place_id, embedding 
            FROM {self.table_name} 
            WHERE place_id IN ({placeholders})
            """
            
            cursor.execute(query, place_ids)
            rows = cursor.fetchall()
            
            for place_id, embedding_str in rows:
                # Convert TiDB VECTOR format back to list of floats
                embedding_str = embedding_str.strip('[]')
                embedding = [float(x.strip()) for x in embedding_str.split(',')]
                results.append((place_id, embedding))
            
            logger.info(f"Retrieved {len(results)} embeddings out of {len(place_ids)} requested")
            return results
            
        except mysql.connector.Error as err:
            logger.error(f"Error searching embeddings: {err}")
            return results
        finally:
            cursor.close()
            connection.close()