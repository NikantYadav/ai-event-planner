"""
Data models for vendors.
"""
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

from src.utils.logger import get_logger

logger = get_logger(__name__)

@dataclass
class VendorData:
    """Class for storing vendor data in a structured format."""
    
    # Google Places fields
    place_id: str
    google_id: str
    name: str
    display_name: Dict[str, Any]
    latitude: float
    longitude: float
    formatted_address: str
    short_formatted_address: str
    plus_code_global: Optional[str] = None
    plus_code_compound: Optional[str] = None
    primary_type: Optional[str] = None
    business_types: List[str] = field(default_factory=list)
    rating: Optional[float] = None
    user_rating_count: int = 0
    price_level: Optional[int] = None
    business_status: Optional[str] = None
    national_phone: Optional[str] = None
    international_phone: Optional[str] = None
    website_uri: Optional[str] = None
    google_maps_uri: Optional[str] = None
    delivery: bool = False
    takeout: bool = False
    opening_hours: Dict[str, Any] = field(default_factory=dict)
    utc_offset_minutes: Optional[int] = None
    accepts_cash_only: bool = False
    accepts_nfc: bool = False
    accepts_credit_cards: bool = False
    photos_count: int = 0
    specialties: str = "general decoration"
    embedding: Optional[List[float]] = None
    
    @classmethod
    def from_place_data(cls, place: Dict[str, Any]) -> 'VendorData':
        """
        Create a VendorData instance from Google Places API response.
        
        Args:
            place (Dict[str, Any]): Place data from Google Places API.
            
        Returns:
            VendorData: Structured vendor data.
        """
        location = place.get('location', {})
        display_name = place.get('displayName', {})
        plus_code = place.get('plusCode', {})
        payment_options = place.get('paymentOptions', {})
        
        # Extract specialties from business info
        specialties = cls._extract_specialties(place)
        
        return cls(
            place_id=place.get('id'),
            google_id=place.get('id'),
            name=display_name.get('text', ''),
            display_name=display_name,
            latitude=location.get('latitude'),
            longitude=location.get('longitude'),
            formatted_address=place.get('formattedAddress'),
            short_formatted_address=place.get('shortFormattedAddress'),
            plus_code_global=plus_code.get('globalCode'),
            plus_code_compound=plus_code.get('compoundCode'),
            primary_type=place.get('primaryType'),
            business_types=place.get('types', []),
            rating=place.get('rating'),
            user_rating_count=place.get('userRatingCount', 0),
            price_level=place.get('priceLevel'),
            business_status=place.get('businessStatus'),
            national_phone=place.get('nationalPhoneNumber'),
            international_phone=place.get('internationalPhoneNumber'),
            website_uri=place.get('websiteUri'),
            google_maps_uri=place.get('googleMapsUri'),
            delivery=place.get('delivery', False),
            takeout=place.get('takeout', False),
            opening_hours=place.get('regularOpeningHours', {}),
            utc_offset_minutes=place.get('utcOffsetMinutes'),
            accepts_cash_only=payment_options.get('acceptsCashOnly', False),
            accepts_nfc=payment_options.get('acceptsNfc', False),
            accepts_credit_cards=payment_options.get('acceptsCreditCards', False),
            photos_count=len(place.get('photos', [])),
            specialties=specialties
        )
    
    @staticmethod
    def _extract_specialties(place: Dict[str, Any]) -> str:
        """
        Extract decoration specialties from business info.
        
        Args:
            place (Dict[str, Any]): Place data from Google Places API.
            
        Returns:
            str: Comma-separated specialties.
        """
        types = place.get('types', [])
        name = place.get('displayName', {}).get('text', '').lower()
        
        specialties = []
        
        # Check business types
        if 'florist' in types:
            specialties.append('flower decoration')
        if 'event_planner' in types:
            specialties.append('event planning')
        
        # Check name for keywords
        if 'balloon' in name:
            specialties.append('balloon decoration')
        if 'flower' in name or 'floral' in name:
            specialties.append('flower arrangement')
        if 'wedding' in name:
            specialties.append('wedding decoration')
        if 'birthday' in name or 'party' in name:
            specialties.append('party decoration')
        
        return ', '.join(specialties) if specialties else 'general decoration'
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the vendor data to a dictionary suitable for database storage.
        
        Returns:
            Dict[str, Any]: Dictionary representation of vendor data.
        """
        return {
            'place_id': self.place_id,
            'google_id': self.google_id,
            'name': self.name,
            'display_name': json.dumps(self.display_name),
            'latitude': self.latitude,
            'longitude': self.longitude,
            'formatted_address': self.formatted_address,
            'short_formatted_address': self.short_formatted_address,
            'plus_code_global': self.plus_code_global,
            'plus_code_compound': self.plus_code_compound,
            'primary_type': self.primary_type,
            'business_types': json.dumps(self.business_types),
            'rating': self.rating,
            'user_rating_count': self.user_rating_count,
            'price_level': self.price_level,
            'business_status': self.business_status,
            'national_phone': self.national_phone,
            'international_phone': self.international_phone,
            'website_uri': self.website_uri,
            'google_maps_uri': self.google_maps_uri,
            'delivery': self.delivery,
            'takeout': self.takeout,
            'opening_hours': json.dumps(self.opening_hours),
            'utc_offset_minutes': self.utc_offset_minutes,
            'accepts_cash_only': self.accepts_cash_only,
            'accepts_nfc': self.accepts_nfc,
            'accepts_credit_cards': self.accepts_credit_cards,
            'photos_count': self.photos_count,
            'specialties': self.specialties,
            'embedding': json.dumps(self.embedding) if self.embedding else None
        }
    
    def create_embedding_text(self) -> str:
        """
        Create rich text for embedding generation with comprehensive vendor information.
        
        Returns:
            str: Enhanced text representation for embedding generation.
        """
        # Create rich embedding text for better matching
        embedding_text_parts = [
            self.name,
            self.specialties,
            self.primary_type or '',
            f"Business types: {', '.join(self.business_types)}" if self.business_types else "",
            self.formatted_address or '',
            self.short_formatted_address or '',
            f"Rating: {self.rating}" if self.rating else "",
            f"Reviews: {self.user_rating_count}" if self.user_rating_count else "",
            f"Price level: {self.price_level}" if self.price_level is not None else "",
            f"Status: {self.business_status}" if self.business_status else "",
        ]
        
        return ' '.join(filter(None, embedding_text_parts))
