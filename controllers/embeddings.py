import requests
from typing import List, Dict, Any, Optional, Union
import time
import numpy as np
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

from utils.logger import get_logger
from utils.config import Config

logger = get_logger(__name__)


class GeminiEmbeddingsAPI:
    """Interface for Google Gemini Embeddings API."""
    
    def __init__(self):
        self.api_key = Config.GEMINI_API_KEY
        self.model = Config.GEMINI_EMBEDDING_MODEL or "gemini-embedding-001"
        self.api_url = "https://generativelanguage.googleapis.com/v1beta/models/{model}:embedContent"
        
        # Rate limiting using sliding window
        self.rpm = Config.RPM
        self.request_timestamps = []  # Track timestamps of requests in the last minute
        self.lock = threading.Lock()
        
        logger.info(f"Initialized Gemini Embeddings API with model: {self.model}, RPM: {self.rpm}")
        if not self.api_key:
            logger.error("GEMINI_API_KEY not found in configuration")
        
    def _wait_for_rate_limit(self):
        """Wait if necessary to respect rate limits using sliding window approach"""
        with self.lock:
            now = time.time()
            
            # Remove timestamps older than 60 seconds (sliding window)
            cutoff_time = now - 60.0
            self.request_timestamps = [ts for ts in self.request_timestamps if ts > cutoff_time]
            
            # Check if we can make a request
            if len(self.request_timestamps) >= self.rpm:
                # Find the oldest request in the current window
                oldest_request = min(self.request_timestamps)
                sleep_time = 60.0 - (now - oldest_request) + 0.1  # Add small buffer
                
                logger.warning(f"Rate limit reached ({len(self.request_timestamps)}/{self.rpm} requests in last 60s), waiting {sleep_time:.2f} seconds")
                time.sleep(sleep_time)
                
                # Clean up timestamps again after waiting
                now = time.time()
                cutoff_time = now - 60.0
                self.request_timestamps = [ts for ts in self.request_timestamps if ts > cutoff_time]
            
            # Record this request
            self.request_timestamps.append(now)
            logger.debug(f"Rate limit check passed, {len(self.request_timestamps)}/{self.rpm} requests in last 60s")

    def generate_embedding(self, text: Union[str, List[str]],
                           output_dimensionality: Optional[int] = 1536) -> Optional[Union[List[float], List[List[float]]]]:
        """Generate embeddings for text using Google Gemini Embeddings API."""
        start_time = time.time()
        try:
            # Apply rate limiting
            self._wait_for_rate_limit()
            
            # Handle both single string and list of strings
            input_text = [text] if isinstance(text, str) else text
            text_preview = (input_text[0][:50] + "...") if len(input_text[0]) > 50 else input_text[0]
            logger.info(f"Generating embedding for text: '{text_preview}' (dim: {output_dimensionality})")
            
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
            
            logger.debug(f"Making API request to Gemini Embeddings API")
            response = requests.post(url, headers=headers, json=data)
            api_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                logger.debug(f"API request successful in {api_time:.2f}s")
                
                # Extract embeddings from response
                if 'embedding' in result:
                    embeddings = result['embedding']['values']
                    logger.info(f"Generated embedding with {len(embeddings)} dimensions")
                    
                    # If output_dimensionality is provided and not 3072, normalize the embeddings
                    if output_dimensionality and output_dimensionality != 3072:
                        embeddings = self._normalize_embedding(embeddings)
                        logger.debug(f"Normalized embedding to unit norm")
                        
                    # Return single embedding for single text input
                    return embeddings if isinstance(text, str) else embeddings
                elif 'embeddings' in result:
                    # Handle multiple embeddings
                    embeddings_list = [emb['values'] for emb in result['embeddings']]
                    logger.info(f"Generated {len(embeddings_list)} embeddings")
                    
                    if output_dimensionality and output_dimensionality != 3072:
                        embeddings_list = [self._normalize_embedding(emb) for emb in embeddings_list]
                        logger.debug(f"Normalized {len(embeddings_list)} embeddings to unit norm")
                        
                    return embeddings_list[0] if len(embeddings_list) == 1 and isinstance(text, str) else embeddings_list
                else:
                    logger.error(f"Unexpected response from Gemini API: {result}")
                    return None
            else:
                logger.error(f"Gemini API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            total_time = time.time() - start_time
            logger.error(f"Error generating Gemini embedding after {total_time:.2f}s: {e}")
            return None
            
    def _normalize_embedding(self, embedding: List[float]) -> List[float]:
        """Normalize an embedding vector to have unit norm (length of 1)."""
        try:
            embedding_np = np.array(embedding)
            norm = np.linalg.norm(embedding_np)
            if norm > 0:
                normalized = embedding_np / norm
                logger.debug(f"Normalized embedding from norm {norm:.4f} to 1.0")
                return normalized.tolist()
            else:
                logger.warning("Cannot normalize embedding with zero norm")
                return embedding
        except Exception as e:
            logger.error(f"Error normalizing embedding: {e}")
            return embedding

    def generate_embeddings_batch(self, texts: List[str], max_workers: int = 5) -> List[Optional[List[float]]]:
        """Generate embeddings for multiple texts concurrently"""
        if not texts:
            logger.warning("No texts provided for batch embedding generation")
            return []
        
        start_time = time.time()
        logger.info(f"Starting batch embedding generation for {len(texts)} texts using {max_workers} workers")
        
        results = [None] * len(texts)
        completed_count = 0
        
        def generate_single_embedding(index: int, text: str) -> tuple:
            nonlocal completed_count
            try:
                embedding = self.generate_embedding(text)
                completed_count += 1
                if completed_count % 10 == 0 or completed_count == len(texts):
                    logger.info(f"Batch progress: {completed_count}/{len(texts)} embeddings completed")
                return (index, embedding)
            except Exception as e:
                logger.error(f"Error generating embedding for batch item {index}: {e}")
                return (index, None)
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            logger.debug(f"Submitting {len(texts)} embedding tasks to thread pool")
            future_to_index = {
                executor.submit(generate_single_embedding, i, text): i 
                for i, text in enumerate(texts)
            }
            
            for future in as_completed(future_to_index):
                try:
                    index, result = future.result()
                    results[index] = result
                except Exception as e:
                    index = future_to_index[future]
                    logger.error(f"Error processing embedding batch item {index}: {e}")
                    results[index] = None
        
        successful_count = sum(1 for r in results if r is not None)
        failed_count = len(texts) - successful_count
        total_time = time.time() - start_time
        
        logger.info(f"Batch embedding completed in {total_time:.2f}s: {successful_count} successful, {failed_count} failed")
        if failed_count > 0:
            logger.warning(f"Failed to generate {failed_count} embeddings out of {len(texts)}")
        
        return results