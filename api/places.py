"""
Google Places API integration for retrieving vendor data.
"""
import requests
import time
from typing import Dict, Any, List
import json

from utils.logger import get_logger
from utils.config import Config

logger = get_logger(__name__)

class GooglePlacesAPI:
    """Interface for Google Places API."""
    
    def __init__(self):
        self.api_key = Config.GOOGLE_MAPS_API_KEY
        self.field_mask = Config.PLACES_FIELD_MASK
    
    def search_places(self, query: str, location_bias: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Search for places using the Google Places API.
        """
        url = Config.GOOGLE_PLACES_BASE_URL
        
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
                logger.error(f"{response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"'{query}': {e}")
            return []

#check if works
import json

def main():
    # Instantiate the API client
    api = GooglePlacesAPI()
    # Example query (you can change this to test other vendors/places)
    query = "Banquet hall in Gurugram"
    
    # Call the search method
    results = api.search_places(query)
    
    # Print results
    if results:
        print(f"✅ Found {len(results)} places for query: '{query}'")
        for i, place in enumerate(results[:5], start=1):  # Show first 5 results
            print(f"\n=== Result {i} ===")
            print(json.dumps(place, indent=2))  # Pretty print full JSON
    else:
        print("⚠️ No results found or error occurred.")

# Run main when executed directly
if __name__ == "__main__":
    main()
