"""
Database operations for the Event Planner application.
"""
import mysql.connector
import json
from typing import Dict, Any, List, Optional
import time

from src.utils.logger import get_logger
from src.utils.config import Config

logger = get_logger(__name__)

class Database:
    """Database access layer for the application."""
    
    def __init__(self):
        self.db_config = Config.DB_CONFIG
    
    def get_connection(self):
        """
        Get a connection to the database.
        
        Returns:
            mysql.connector.connection.MySQLConnection: Database connection object.
        """
        try:
            return mysql.connector.connect(**self.db_config)
        except mysql.connector.Error as err:
            logger.error(f"❌ Database connection error: {err}")
            raise
    
    def save_vendors(self, vendors: List[Dict[str, Any]]):
        """
        Save vendors to the database.
        
        Args:
            vendors (List[Dict[str, Any]]): List of vendor data to save.
        
        Returns:
            int: Number of successfully inserted vendors.
        """
        connection = self.get_connection()
        cursor = connection.cursor()
        
        insert_query = """
            INSERT INTO gurugram_decoration_vendors 
            (place_id, google_id, name, display_name, latitude, longitude, 
             formatted_address, short_formatted_address, plus_code_global, plus_code_compound,
             primary_type, business_types, rating, user_rating_count, price_level, 
             business_status, national_phone, international_phone, website_uri, 
             google_maps_uri, delivery, takeout, opening_hours, utc_offset_minutes,
             accepts_cash_only, accepts_nfc, accepts_credit_cards, photos_count, 
             specialties, embedding)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE 
            rating = VALUES(rating), 
            user_rating_count = VALUES(user_rating_count),
            embedding = VALUES(embedding),
            updated_at = CURRENT_TIMESTAMP
        """
        
        successful_inserts = 0
        
        for vendor in vendors:
            try:
                values = tuple(list(vendor.values()))
                cursor.execute(insert_query, values)
                successful_inserts += 1
                logger.info(f"✅ Saved: {vendor.get('name', 'Unknown')}")
                
            except Exception as e:
                logger.error(f"❌ Error saving {vendor.get('name', 'Unknown')}: {e}")
        
        connection.commit()
        cursor.close()
        connection.close()
        
        logger.info(f"\n🎉 Successfully saved {successful_inserts}/{len(vendors)} vendors!")
        return successful_inserts

    def get_vendors_with_embeddings(self) -> List[Dict[str, Any]]:
        """
        Retrieve all vendors that have embeddings from the database.
        
        Returns:
            List[Dict[str, Any]]: List of vendor data with embeddings.
        """
        try:
            connection = self.get_connection()
            cursor = connection.cursor(dictionary=True)
            
            query = """
                SELECT place_id, name, formatted_address, rating, user_rating_count, 
                       website_uri, national_phone, international_phone, google_maps_uri,
                       specialties, embedding, primary_type, business_types, latitude, longitude
                FROM gurugram_decoration_vendors 
                WHERE embedding IS NOT NULL
                ORDER BY rating DESC
            """
            cursor.execute(query)
            vendors = cursor.fetchall()
            
            cursor.close()
            connection.close()
            
            logger.info(f"📊 Retrieved {len(vendors)} vendors with embeddings")
            return vendors
            
        except Exception as e:
            logger.error(f"❌ Error retrieving vendors with embeddings: {e}")
            return []

    def count_vendors(self) -> int:
        """
        Count total number of vendors in the database.
        
        Returns:
            int: Total number of vendors.
        """
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM gurugram_decoration_vendors")
            count = cursor.fetchone()[0]
            
            cursor.close()
            connection.close()
            
            return count
            
        except Exception as e:
            logger.error(f"❌ Error counting vendors: {e}")
            return 0
