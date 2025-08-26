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
            'X-Goog-FieldMask': "places.id"
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

    def get_place_details(self, place_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific place using its Place ID.
        """
        url = f"https://places.googleapis.com/v1/places/{place_id}"
        
        headers = {
            'Content-Type': 'application/json',
            'X-Goog-Api-Key': self.api_key,
            'X-Goog-FieldMask': 'displayName,reviews,generativeSummary,primaryType,types'
        }
        
        try:
            logger.info(f"Fetching details for place: {place_id}")
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"API error: {response.status_code} - {response.text}")
                return {}
                
        except Exception as e:
            logger.error(f"Error fetching details for place '{place_id}': {e}")
            return {}

    def search_places_with_details(self, query: str, location_bias: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Search for places using the Google Places API and fetch details for each place.
        
        Args:
            query (str): The search query.
            location_bias (Dict[str, Any], optional): Location bias parameters.
        
        Returns:
            List[Dict[str, Any]]: List of detailed place information.
        """
        base_url = Config.GOOGLE_PLACES_BASE_URL
        
        headers = {
            'Content-Type': 'application/json',
            'X-Goog-Api-Key': self.api_key,
            'X-Goog-FieldMask': "places.id"
        }
        
        # Use provided location bias or default to Gurugram bounds
        if not location_bias:
            location_bias = {"rectangle": Config.GURUGRAM_BOUNDS}
        
        data = {
            "textQuery": query,
            "locationBias": location_bias
        }
        
        try:
            logger.info(f"🔍 Searching: {query}")
            response = requests.post(base_url, headers=headers, json=data)
            
            if response.status_code != 200:
                logger.error(f"❌ API error: {response.status_code} - {response.text}")
                return []
            
            results = response.json().get('places', [])
            detailed_results = []
            
            # Fetch details for each place ID
            for place in results:
                place_id = place.get("id")
                if not place_id:
                    continue
                
                detail_url = f"https://places.googleapis.com/v1/places/{place_id}"
                detail_headers = {
                    'Content-Type': 'application/json',
                    'X-Goog-Api-Key': self.api_key,
                    'X-Goog-FieldMask': 'displayName,reviews,generativeSummary,primaryType,types'
                }
                
                detail_resp = requests.get(detail_url, headers=detail_headers)
                if detail_resp.status_code == 200:
                    detail_data=detail_resp.json()
                    detail_data["place_id"]=place_id
                    detailed_results.append(detail_data)
                else:
                    logger.warning(f"⚠️ Could not fetch details for {place_id}: {detail_resp.text}")
            
            return detailed_results
        
        except Exception as e:
            logger.error(f"❌ Error searching '{query}': {e}")
            return []



def main():
    # Instantiate the API client
    api = GooglePlacesAPI()
    # Example query (you can change this to test other vendors/places)
    query = "Banquet hall in Gurugram"
    
    # Call the search method
    results = api.search_places_with_details(query)
    #results = api.get_place_details("ChIJEe-pDbYeDTkRmu3RMlwjWNY")
    # Print results
    if results:
        #print(f"Results : {results}")
        print(f"✅ Found {len(results)} places for query: '{query}'")
        for i, place in enumerate(results[:5], start=1):  # Show first 5 results
            print(f"\n=== Result {i} ===")
            print(json.dumps(place, indent=2))  # Pretty print full JSON
    else:
        print("⚠️ No results found or error occurred.")

# Run main when executed directly
if __name__ == "__main__":
    main()
