"""
Google Places API integration for retrieving vendor data.
"""
import requests
import time
from typing import Dict, Any, List
import json

from src.utils.logger import get_logger
from src.utils.config import Config

logger = get_logger(__name__)

class GooglePlacesAPI:
    """Interface for Google Places API."""
    
    def __init__(self):
        self.api_key = Config.GOOGLE_MAPS_API_KEY
        self.field_mask = Config.PLACES_FIELD_MASK
    
    def search_places(self, query: str, location_bias: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Search for places using the Google Places API.
        
        Args:
            query (str): The search query.
            location_bias (Dict[str, Any], optional): Location bias parameters. 
                Defaults to Gurugram boundaries.
        
        Returns:
            List[Dict[str, Any]]: List of places matching the query.
        """
        url = "https://places.googleapis.com/v1/places:searchText"
        
        headers = {
            'Content-Type': 'application/json',
            'X-Goog-Api-Key': self.api_key,
            'X-Goog-FieldMask': self.field_mask
        }
        
        # Use provided location bias or default to Gurugram bounds
        if not location_bias:
            location_bias = {
                "rectangle": Config.GURUGRAM_BOUNDS
            }
        
        data = {
            "textQuery": query,
            "locationBias": location_bias
        }
        
        try:
            logger.info(f"🔍 Searching: {query}")
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code == 200:
                results = response.json()
                return results.get('places', [])
            else:
                logger.error(f"❌ API error: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"❌ Error searching '{query}': {e}")
            return []
    