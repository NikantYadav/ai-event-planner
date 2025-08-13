"""
Voyage AI API and Google Gemini API integration for generating embeddings.
"""
import requests
from typing import List, Dict, Any, Optional, Union
import time
import numpy as np
import threading

from src.utils.logger import get_logger
from src.utils.config import Config

logger = get_logger(__name__)

class VoyageEmbeddingsAPI:
    """Interface for Voyage AI Embeddings API."""
    
    def __init__(self):
        self.api_key = Config.VOYAGE_API_KEY
        self.model = Config.EMBEDDING_MODEL  # Should be "voyage-3.5" or another supported model
        self.api_url = "https://api.voyageai.com/v1/embeddings"
    
    def generate_embedding(self, text: Union[str, List[str]]) -> Optional[Union[List[float], List[List[float]]]]:
        """
        Generate embedding for text using Voyage AI Embeddings API.
        
        Args:
            text (Union[str, List[str]]): The text or texts to generate embedding(s) for.
        
        Returns:
            Optional[Union[List[float], List[List[float]]]]: The embedding(s) as a list of floats or list of lists,
            or None if an error occurs.
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Handle both single string and list of strings
            input_text = [text] if isinstance(text, str) else text
            
            data = {
                "input": input_text,
                "model": self.model
            }
            
            response = requests.post(self.api_url, headers=headers, json=data)
            
            if response.status_code == 200:
                result = response.json()
                # Extract the embedding(s) from the response
                if 'data' in result and len(result['data']) > 0:
                    embeddings = [item['embedding'] for item in result['data']]
                    # Return single embedding or list based on input
                    return embeddings[0] if isinstance(text, str) else embeddings
                else:
                    logger.error(f"❌ Unexpected response structure: {result}")
                    return None
            else:
                logger.error(f"❌ Voyage AI API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error generating Voyage AI embedding: {e}")
            return None

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
        
        Args:
            text (Union[str, List[str]]): The text or texts to generate embedding(s) for.
            task_type (Optional[str]): The task type to optimize embeddings for. Defaults to SEMANTIC_SIMILARITY.
                Other options include:
                - CLASSIFICATION: For classifying texts
                - CLUSTERING: For clustering texts
                - RETRIEVAL_DOCUMENT: For document search
                - RETRIEVAL_QUERY: For search queries
                - CODE_RETRIEVAL_QUERY: For code search
                - QUESTION_ANSWERING: For QA systems
                - FACT_VERIFICATION: For fact-checking
            output_dimensionality (Optional[int]): The size of output embedding vector.
                Recommended values: 768, 1536, 3072 (default)
        
        Returns:
            Optional[Union[List[float], List[List[float]]]]: The embedding(s) as a list of floats or list of lists,
            or None if an error occurs.
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
                    
                    # If output_dimensionality is provided and not 3072, normalize the embeddings
                    if output_dimensionality and output_dimensionality != 3072:
                        embeddings_list = [self._normalize_embedding(emb) for emb in embeddings_list]
                        
                    return embeddings_list[0] if len(embeddings_list) == 1 and isinstance(text, str) else embeddings_list
                else:
                    logger.error(f"❌ Unexpected response structure from Gemini API: {result}")
                    return None
            else:
                logger.error(f"❌ Gemini API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error generating Gemini embedding: {e}")
            return None
            
    def _normalize_embedding(self, embedding: List[float]) -> List[float]:
        """
        Normalize an embedding vector to have unit norm (length of 1).
        This is recommended for embeddings with dimensions other than 3072.
        
        Args:
            embedding (List[float]): The embedding vector to normalize.
            
        Returns:
            List[float]: The normalized embedding vector.
        """
        embedding_np = np.array(embedding)
        norm = np.linalg.norm(embedding_np)
        if norm > 0:
            normalized = embedding_np / norm
            return normalized.tolist()
        return embedding