"""
Vendor collector service that coordinates the collection, enrichment,
and storage of vendor data.
"""
from typing import Dict, Any, List, Optional
import time
from datetime import datetime

from src.api.places import GooglePlacesAPI
from src.api.embeddings import VoyageEmbeddingsAPI
from src.api.embeddings import GeminiEmbeddingsAPI
from src.db.database import Database
from src.models.vendor import VendorData
from src.utils.logger import get_logger

logger = get_logger(__name__)

class VendorCollectorService:
    """Service for collecting, enriching, and storing vendor data."""
    
    def __init__(self):
        self.places_api = GooglePlacesAPI()
        self.voyage_embeddings_api = VoyageEmbeddingsAPI()
        self.gemini_embeddings_api = GeminiEmbeddingsAPI()
        self.db = Database()
        
    def collect_decoration_vendors(self):
        """
        Collect decoration vendors from Google Places API, 
        enrich with Voyage embeddings, and save to database.
        """
        # Define search queries for decoration vendors in Gurugram/Gurgaon
        search_queries = [
            "balloon decoration services Gurugram",
            "event decoration Gurgaon",
        ]
        

        # Step 1: Search for places
        logger.info("🔎 Searching for decoration vendors...")
        raw_vendors = []
        for query in search_queries:
            try:
                results = self.places_api.search_places(query)
                if results:
                    raw_vendors.extend(results)
            except Exception as e:
                logger.error(f"❌ Error searching for '{query}': {e}")
        
        if not raw_vendors:
            logger.warning("❌ No vendors found!")
            return
        
        # Step 2: Extract and structure data
        logger.info(f"\n📊 Processing {len(raw_vendors)} vendors...")
        vendors = []
        
        for place in raw_vendors:
            try:
                # Create structured vendor data from raw place data
                vendor = VendorData.from_place_data(place)
                vendors.append(vendor)
            except Exception as e:
                logger.error(f"❌ Error processing vendor: {e}")
        
        # Step 3: Generate embeddings for each vendor
        logger.info(f"\n🧠 Generating Voyage embeddings for {len(vendors)} vendors...")
        for vendor in vendors:
            try:
                # Create rich text for embedding
                embedding_text = vendor.create_embedding_text()
                
                # Generate embedding using Voyage API
                #embedding = self.voyage_embeddings_api.generate_embedding(embedding_text)
                # Generate embedding using Gemini API (with built-in rate limiting)
                embedding = self.gemini_embeddings_api.generate_embedding(embedding_text, output_dimensionality=1536)
                
                if embedding:
                    vendor.embedding = embedding
                    logger.info(f"✅ Generated embedding for: {vendor.name}")
                else:
                    logger.warning(f"⚠️ Failed to generate embedding for: {vendor.name}")
                    
                # No need for manual delay - rate limiting is handled by the API class
                
            except Exception as e:
                logger.error(f"❌ Error generating embedding for {vendor.name}: {e}")
        
        # Step 4: Convert to database format and save
        if vendors:
            logger.info(f"\n💾 Saving {len(vendors)} vendors to database...")
            vendor_dicts = [v.to_dict() for v in vendors]
            self.db.save_vendors(vendor_dicts)
            
            # Save a backup copy of collected data
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"vendors_collected_{timestamp}.json"
            
            # Create a JSON serializable version of vendor data
            serializable_vendors = []
            for vendor in vendors:
                v_dict = vendor.to_dict()
                # Make sure embedding is serialized if present
                if isinstance(v_dict.get('embedding'), str):
                    try:
                        v_dict['embedding'] = f"<Embedding vector with {len(vendor.embedding)} dimensions>"
                    except:
                        v_dict['embedding'] = None
                serializable_vendors.append(v_dict)
            
            self._save_backup(serializable_vendors, filename)
        
        logger.info("🎯 Collection completed!")
    
    def _save_backup(self, data: List[Dict[str, Any]], filename: str):
        """Save data as a backup JSON file."""
        import json
        
        try:
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"📁 Backup saved to {filename}")
        except Exception as e:
            logger.error(f"❌ Error saving backup: {e}")
