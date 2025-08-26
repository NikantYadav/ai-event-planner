import requests
from typing import List, Dict, Any, Optional, Union
import time
import numpy as np
import threading

from utils.logger import get_logger
from utils.config import Config

logger = get_logger(__name__)


class GeminiEmbeddingsAPI:
    """Interface for Google Gemini Embeddings API."""
    
    def __init__(self):
        self.api_key = Config.GEMINI_API_KEY
        self.model = Config.GEMINI_EMBEDDING_MODEL or "gemini-embedding-001"
        self.api_url = "https://generativelanguage.googleapis.com/v1beta/models/{model}:embedContent"
        
        # Rate limiting: 100 requests per minute (100 RPM)
        self.rate_limit = 100  # requests
        self.period = 60  # seconds
        self.tokens = self.rate_limit  # Initially full bucket
        self.last_refill_time = time.time()
        self.lock = threading.Lock()
        
    def _refill_token_bucket(self):
        """Refill the token bucket based on elapsed time"""
        now = time.time()
        time_passed = now - self.last_refill_time
        
        # Calculate how many tokens to add based on time passed
        new_tokens = time_passed * (self.rate_limit / self.period)
        
        # Add tokens to the bucket, up to the max capacity
        with self.lock:
            self.tokens = min(self.rate_limit, self.tokens + new_tokens)
            self.last_refill_time = now
    
    def _consume_token(self):
        """Try to consume a token from the bucket. If no tokens are available, wait."""
        while True:
            self._refill_token_bucket()
            
            with self.lock:
                if self.tokens >= 1:
                    self.tokens -= 1
                    return
            
            # If no tokens available, wait a bit before checking again
            # Sleep for a fraction of the period to achieve better throughput
            sleep_time = self.period / (self.rate_limit * 2)
            logger.debug(f"Rate limit reached, waiting {sleep_time:.2f} seconds...")
            time.sleep(sleep_time)
        
    def generate_embedding(self, text: Union[str, List[str]],
                           output_dimensionality: Optional[int] = 1536) -> Optional[Union[List[float], List[List[float]]]]:
        """
        Generate embeddings for text using Google Gemini Embeddings API.
        """
        try:
            # Apply rate limiting - consume a token from the bucket
            self._consume_token()
            
            # Handle both single string and list of strings
            input_text = [text] if isinstance(text, str) else text
            
            # Construct the API URL with the model
            url = self.api_url.format(model=self.model)
            url = f"{url}?key={self.api_key}"
            
            # Prepare request data
            data = {
                "model": self.model,
                "content": {
                    "parts": [{"text": t} for t in input_text]
                }
            }
            
            # Add output_dimensionality if provided
            if output_dimensionality:
                data["outputDimensionality"] = output_dimensionality
            
            headers = {
                "Content-Type": "application/json"
            }
            
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code == 200:
                result = response.json()
                
                # Extract embeddings from response
                if 'embedding' in result:
                    embeddings = result['embedding']['values']
                    
                    # If output_dimensionality is provided and not 3072, normalize the embeddings
                    if output_dimensionality and output_dimensionality != 3072:
                        embeddings = self._normalize_embedding(embeddings)
                        
                    # Return single embedding for single text input
                    return embeddings if isinstance(text, str) else embeddings
                elif 'embeddings' in result:
                    # Handle multiple embeddings
                    embeddings_list = [emb['values'] for emb in result['embeddings']]
                    
                    if output_dimensionality and output_dimensionality != 3072:
                        embeddings_list = [self._normalize_embedding(emb) for emb in embeddings_list]
                        
                    return embeddings_list[0] if len(embeddings_list) == 1 and isinstance(text, str) else embeddings_list
                else:
                    logger.error(f" Unexpected response from Gemini API: {result}")
                    return None
            else:
                logger.error(f"Gemini API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error generating Gemini embedding: {e}")
            return None
            
    def _normalize_embedding(self, embedding: List[float]) -> List[float]:
        """
        Normalize an embedding vector to have unit norm (length of 1).
        """
        embedding_np = np.array(embedding)
        norm = np.linalg.norm(embedding_np)
        if norm > 0:
            normalized = embedding_np / norm
            return normalized.tolist()
        return embedding