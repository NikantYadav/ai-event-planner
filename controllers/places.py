import requests
import time
from typing import Dict, Any, List
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

from utils.logger import get_logger
from utils.config import Config

logger = get_logger(__name__)

class GooglePlacesAPI:
    """Interface for Google Places API."""
    
    def __init__(self):
        self.api_key = Config.GOOGLE_MAPS_API_KEY
        self.field_mask = Config.PLACES_FIELD_MASK

    def _fetch_place_details(self, place_id: str) -> Dict[str, Any]:
        """Fetch details for a single place ID"""
        try:
            time.sleep(60 / Config.RPM)  # Simple rate limiting based on RPM
            
            detail_url = f"https://places.googleapis.com/v1/places/{place_id}"
            detail_headers = {
                'Content-Type': 'application/json',
                'X-Goog-Api-Key': self.api_key,
                'X-Goog-FieldMask': 'displayName,reviews,generativeSummary,primaryType,types'
            }
            
            detail_resp = requests.get(detail_url, headers=detail_headers)
            if detail_resp.status_code == 200:
                detail_data = detail_resp.json()
                detail_data["place_id"] = place_id
                return detail_data
            else:
                logger.warning(f"Could not fetch details for {place_id}: {detail_resp.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching details for place {place_id}: {e}")
            return None

    def search_places_with_details(self, query: str, location_bias: Dict[str, Any] = None, max_workers: int = 5) -> List[Dict[str, Any]]:
        """Search for places using the Google Places API and fetch details for each place concurrently."""
        base_url = Config.GOOGLE_PLACES_BASE_URL
        
        headers = {
            'Content-Type': 'application/json',
            'X-Goog-Api-Key': self.api_key,
            'X-Goog-FieldMask': "places.id"
        }
        
        if not location_bias:
            logger.error("No location bias provided")
            return []
        
        data = {
            "textQuery": query,
            "locationBias": location_bias
        }
        
        try:
            response = requests.post(base_url, headers=headers, json=data)
            
            if response.status_code != 200:
                logger.error(f"API error: {response.status_code} - {response.text}")
                return []
            
            results = response.json().get('places', [])
            place_ids = [place.get("id") for place in results if place.get("id")]
            
            if not place_ids:
                logger.warning(f"No place IDs found for query: {query}")
                return []
            
            # Fetch details for all places concurrently
            detailed_results = []
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_place_id = {
                    executor.submit(self._fetch_place_details, place_id): place_id 
                    for place_id in place_ids
                }
                
                for future in as_completed(future_to_place_id):
                    try:
                        result = future.result()
                        if result:
                            detailed_results.append(result)
                    except Exception as e:
                        place_id = future_to_place_id[future]
                        logger.error(f"Error processing place details for {place_id}: {e}")
            
            logger.info(f"Successfully fetched details for {len(detailed_results)}/{len(place_ids)} places")
            return detailed_results
        
        except Exception as e:
            logger.error(f"Error searching '{query}': {e}")
            return []

    def get_location_bounds(self, place_name: str) -> Dict[str, Dict[str, float]]:
        """Fetch bounding box for a given place using Nominatim (OpenStreetMap) API."""
        url = "https://nominatim.openstreetmap.org/search.php"
        params = {
            "q": place_name,
            "format": "json",

        }
        
        try:
            response = requests.get(url, params=params, headers={"User-Agent": "GooglePlacesAPI/1.0"})
            
            if response.status_code != 200:
                logger.error(f"Nominatim API error: {response.status_code} - {response.text}")
                return {}
            
            results = response.json()
            if not results:
                logger.warning(f"No bounding box found for '{place_name}'")
                return {}
            
            # Pick the "best" result (highest importance)
            best_match = max(results, key=lambda x: x.get("importance", 0))
            bbox = best_match.get("boundingbox", None)
            
            if not bbox or len(bbox) != 4:
                logger.warning(f"No valid bounding box for '{place_name}'")
                return {}
            
            # Nominatim gives: [south_lat, north_lat, west_lon, east_lon]
            south_lat, north_lat, west_lon, east_lon = map(float, bbox)
            
            bounds = {
                "low": {"latitude": south_lat, "longitude": west_lon},
                "high": {"latitude": north_lat, "longitude": east_lon}
            }
            
            return bounds
        
        except Exception as e:
            logger.error(f"Error fetching bounds for '{place_name}': {e}")
            return {}