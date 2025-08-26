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