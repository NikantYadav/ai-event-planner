"""
Configuration utilities for the Event Planner application.
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Configuration class for application-wide settings."""
    
    # Google Maps API settings
    GOOGLE_PLACES_BASE_URL="https://places.googleapis.com/v1/places:searchText"
    GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')
    
    # Gemini API settings
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    GEMINI_EMBEDDING_MODEL = 'gemini-embedding-001'
    
    # Voyage AI API settings
    EMBEDDING_MODEL = 'voyage-3.5'
    VOYAGE_API_KEY = os.getenv('VOYAGE_API_KEY')


    # Database settings
    DB_CONFIG = {
        'host': os.getenv('TIDB_HOST'),
        'port': int(os.getenv('TIDB_PORT', 4000)),
        'user': os.getenv('TIDB_USER'),
        'password': os.getenv('TIDB_PASSWORD'),
        'database': os.getenv('TIDB_DATABASE')
    }
    
    # Google Places API field mask
    PLACES_FIELD_MASK = ','.join([
        'places.id', 'places.displayName', 'places.formattedAddress',
        'places.shortFormattedAddress', 'places.location', 'places.primaryType',
        'places.types', 'places.rating', 'places.userRatingCount',
        'places.priceLevel', 'places.businessStatus', 'places.nationalPhoneNumber',
        'places.internationalPhoneNumber', 'places.websiteUri', 'places.googleMapsUri',
        'places.delivery', 'places.takeout', 'places.regularOpeningHours',
        'places.utcOffsetMinutes', 'places.plusCode', 'places.paymentOptions', 'places.photos'
    ])
    
    # Gurugram location boundaries
    GURUGRAM_BOUNDS = {
        "low": {"latitude": 28.3500, "longitude": 76.9000},
        "high": {"latitude": 28.5500, "longitude": 77.1500}
    }
