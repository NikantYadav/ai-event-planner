"""
Event Planner Service that converts user event descriptions to vendor search queries
and finds the most relevant vendors using embedding similarity.
"""
import os
import base64
import numpy as np
from typing import List, Dict, Any, Optional
from google import genai
from google.genai import types

from src.api.embeddings import GeminiEmbeddingsAPI
from src.db.database import Database
from src.utils.logger import get_logger

logger = get_logger(__name__)

class EventPlannerService:
    """Service for converting event descriptions to vendor recommendations."""
    
    def __init__(self):
        self.embeddings_api = GeminiEmbeddingsAPI()
        self.db = Database()
        self.genai_client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
        self.model = "gemini-2.5-flash"
    
    def plan_event(self, event_description: str) -> Dict[str, Any]:
        """
        Plan an event based on the user's description.
        
        Args:
            event_description (str): User's description of the event they want to organize
            
        Returns:
            Dict[str, Any]: Dictionary containing optimized search query and top vendors
        """
        logger.info(f"🎯 Planning event: {event_description}")
        
        # Step 1: Convert event description to optimized search query
        search_query = self._generate_search_query(event_description)
        if not search_query:
            return {"error": "Failed to generate search query"}
        
        logger.info(f"🔍 Generated search query: {search_query}")
        
        # Step 2: Generate embedding for the search query
        query_embedding = self.embeddings_api.generate_embedding(search_query)
        if not query_embedding:
            return {"error": "Failed to generate embedding for search query"}
        
        # Step 3: Find top 20 vendors based on similarity
        top_vendors = self._find_similar_vendors(query_embedding, limit=20)
        
        return {
            "event_description": event_description,
            "search_query": search_query,
            "top_vendors": top_vendors,
            "total_found": len(top_vendors)
        }
    
    def _generate_search_query(self, event_description: str) -> Optional[str]:
        """
        Use Gemini to convert event description to an optimized search query for finding vendors.
        
        Args:
            event_description (str): User's event description
            
        Returns:
            Optional[str]: Optimized search query or None if failed
        """
        try:
            prompt = f"""
            You are an expert event planner. Based on the following event description, generate a concise and specific search query that would be most effective for finding relevant vendors (decorators, caterers, venues, etc.) for this event.

            Event Description: "{event_description}"

            Your task:
            1. Identify the key aspects of the event (type, theme, scale, special requirements)
            2. Create a search query that captures the essential vendor services needed
            3. Include relevant keywords that vendors would use to describe their services
            4. Keep it concise but comprehensive

            Return ONLY the search query, nothing else. The query should be optimized for finding vendors through embeddings similarity search.

            Examples:
            - For "birthday party for 5-year-old with superhero theme": "superhero themed birthday party decorations children entertainment"
            - For "corporate conference for 200 people": "corporate event management conference setup professional catering"
            - For "wedding reception outdoors": "outdoor wedding reception decorations tent rental catering"
            """
            
            contents = [
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=prompt)]
                )
            ]
            
            generate_content_config = types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(thinking_budget=-1)
            )
            
            response_parts = []
            for chunk in self.genai_client.models.generate_content_stream(
                model=self.model,
                contents=contents,
                config=generate_content_config,
            ):
                if chunk.text:
                    response_parts.append(chunk.text)
            
            search_query = ''.join(response_parts).strip()
            return search_query if search_query else None
            
        except Exception as e:
            logger.error(f"❌ Error generating search query with Gemini: {e}")
            return None
    
    def _find_similar_vendors(self, query_embedding: List[float], limit: int = 20) -> List[Dict[str, Any]]:
        """
        Find vendors most similar to the query embedding using cosine similarity.
        
        Args:
            query_embedding (List[float]): The embedding of the search query
            limit (int): Maximum number of vendors to return
            
        Returns:
            List[Dict[str, Any]]: List of vendor data with similarity scores
        """
        try:
            # Get all vendors with embeddings
            vendors = self.db.get_vendors_with_embeddings()
            
            if not vendors:
                logger.warning("⚠️ No vendors with embeddings found in database")
                return []
            
            # Calculate similarities
            query_embedding_np = np.array(query_embedding)
            vendor_similarities = []
            
            for vendor in vendors:
                try:
                    # Parse the embedding JSON
                    vendor_embedding = vendor['embedding']
                    if isinstance(vendor_embedding, str):
                        import json
                        vendor_embedding = json.loads(vendor_embedding)
                    
                    vendor_embedding_np = np.array(vendor_embedding)
                    
                    # Calculate cosine similarity
                    similarity = self._cosine_similarity(query_embedding_np, vendor_embedding_np)
                    
                    # Add similarity score to vendor data
                    vendor_data = dict(vendor)
                    vendor_data['similarity_score'] = float(similarity)
                    vendor_data.pop('embedding')  # Remove embedding from response
                    
                    # Parse business_types if it's a JSON string
                    if isinstance(vendor_data.get('business_types'), str):
                        try:
                            vendor_data['business_types'] = json.loads(vendor_data['business_types'])
                        except:
                            vendor_data['business_types'] = []
                    
                    vendor_similarities.append(vendor_data)
                    
                except Exception as e:
                    logger.error(f"❌ Error processing vendor {vendor.get('name', 'Unknown')}: {e}")
                    continue
            
            # Sort by similarity score (highest first) and return top results
            vendor_similarities.sort(key=lambda x: x['similarity_score'], reverse=True)
            
            top_vendors = vendor_similarities[:limit]
            logger.info(f"✅ Found {len(top_vendors)} similar vendors")
            
            return top_vendors
            
        except Exception as e:
            logger.error(f"❌ Error finding similar vendors: {e}")
            return []
    
    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """
        Calculate cosine similarity between two vectors.
        
        Args:
            a (np.ndarray): First vector
            b (np.ndarray): Second vector
            
        Returns:
            float: Cosine similarity score between -1 and 1
        """
        try:
            # Normalize vectors
            norm_a = np.linalg.norm(a)
            norm_b = np.linalg.norm(b)
            
            if norm_a == 0 or norm_b == 0:
                return 0.0
            
            # Calculate cosine similarity
            similarity = np.dot(a, b) / (norm_a * norm_b)
            return float(similarity)
            
        except Exception as e:
            logger.error(f"❌ Error calculating cosine similarity: {e}")
            return 0.0
