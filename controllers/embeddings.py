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
    """Interface for Google Gemini Embeddings API with support for multiple API keys."""
    
    def __init__(self, user_api_keys: List[str] = None):

        self.api_keys = []
        if Config.GEMINI_API_KEY:
            self.api_keys.append(Config.GEMINI_API_KEY)
        if user_api_keys:
            self.api_keys.extend([key.strip() for key in user_api_keys if key and key.strip()][:5])
        
        if not self.api_keys:
            logger.error("No valid API keys available")
            return


        self.key_usage = {key: {"last_used": 0, "count": 0} for key in self.api_keys}
        self.current_key_index = 0
        
        self.model = Config.GEMINI_EMBEDDING_MODEL or "gemini-embedding-001"
        self.api_url = "https://generativelanguage.googleapis.com/v1beta/models/{model}:embedContent"

        self.rpm = getattr(Config, 'RPM', 60)  
        self.request_timestamps = {}  
        self.lock = threading.Lock()
        
        logger.info(f"Initialized Gemini Embeddings API with model: {self.model}, RPM: {self.rpm}, {len(self.api_keys)} API keys")
        if not self.api_keys:
            logger.error("No API keys available for Gemini Embeddings API")
        
    def _rotate_api_key(self):
        """Rotate to the next available API key based on usage patterns"""
        if len(self.api_keys) <= 1:
            return False
            
        current_time = time.time()
        least_used_index = 0
        least_used_time = current_time
        
        for i, key in enumerate(self.api_keys):
            last_used = self.key_usage[key]["last_used"]
            if current_time - last_used > 60: 
                self.key_usage[key]["count"] = 0 
                
            if last_used < least_used_time:
                least_used_time = last_used
                least_used_index = i

        if least_used_index != self.current_key_index:
            self.current_key_index = least_used_index
            logger.info(f"Rotated to API key {self.current_key_index + 1} for embeddings")
            return True
            
        return False
    
    def _wait_for_rate_limit(self):
        """Wait if necessary to respect rate limits using sliding window approach with key rotation"""
        if not self.api_keys:
            logger.error("No API keys available for rate limiting")
            time.sleep(1)
            return
            
        current_key = self.api_keys[self.current_key_index]
        
        with self.lock:
            now = time.time()
            
            if current_key not in self.request_timestamps:
                self.request_timestamps[current_key] = []
                
            cutoff_time = now - 60.0
            self.request_timestamps[current_key] = [ts for ts in self.request_timestamps[current_key] if ts > cutoff_time]

            if len(self.request_timestamps[current_key]) >= self.rpm:
                if self._rotate_api_key():
                    current_key = self.api_keys[self.current_key_index]
                    if current_key not in self.request_timestamps:
                        self.request_timestamps[current_key] = []
                else:
                    oldest_request = min(self.request_timestamps[current_key])
                    sleep_time = 60.0 - (now - oldest_request) + 0.1  
                    
                    logger.warning(f"Rate limit reached for key {self.current_key_index + 1} " +
                                 f"({len(self.request_timestamps[current_key])}/{self.rpm} requests in last 60s), " +
                                 f"waiting {sleep_time:.2f} seconds")
                    time.sleep(sleep_time)

                    now = time.time()
                    cutoff_time = now - 60.0
                    self.request_timestamps[current_key] = [ts for ts in self.request_timestamps[current_key] if ts > cutoff_time]
            
            self.request_timestamps[current_key].append(now)
            self.key_usage[current_key]["last_used"] = now
            self.key_usage[current_key]["count"] += 1

            if self.key_usage[current_key]["count"] >= 10:
                self._rotate_api_key()
                
            logger.debug(f"Rate limit check passed for key {self.current_key_index + 1}, " +
                        f"{len(self.request_timestamps[current_key])}/{self.rpm} requests in last 60s")

    def generate_embedding(self, text: Union[str, List[str]],
                           output_dimensionality: Optional[int] = 1536) -> Optional[Union[List[float], List[List[float]]]]:
        """Generate embeddings for text using Google Gemini Embeddings API with automatic key rotation."""
        if not self.api_keys:
            logger.error("No API keys available for embedding generation")
            return None
            
        start_time = time.time()
        max_attempts = min(3, len(self.api_keys))
        attempts = 0
        
        while attempts < max_attempts:
            try:
                self._wait_for_rate_limit()

                current_key = self.api_keys[self.current_key_index]
                
                input_text = [text] if isinstance(text, str) else text
                text_preview = (input_text[0][:50] + "...") if len(input_text[0]) > 50 else input_text[0]
                logger.info(f"Generating embedding for text: '{text_preview}' (dim: {output_dimensionality}) with key {self.current_key_index + 1}")
                
                url = self.api_url.format(model=self.model)
                url = f"{url}?key={current_key}"
                
                data = {
                    "model": self.model,
                    "content": {
                        "parts": [{"text": t} for t in input_text]
                    }
                }
            
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
                    
                    if 'embedding' in result:
                        embeddings = result['embedding']['values']
                        logger.info(f"Generated embedding with {len(embeddings)} dimensions")
                        
                        if output_dimensionality and output_dimensionality != 3072:
                            embeddings = self._normalize_embedding(embeddings)
                            logger.debug(f"Normalized embedding to unit norm")
                            
                        return embeddings if isinstance(text, str) else embeddings
                    elif 'embeddings' in result:
                        embeddings_list = [emb['values'] for emb in result['embeddings']]
                        logger.info(f"Generated {len(embeddings_list)} embeddings")
                        
                        if output_dimensionality and output_dimensionality != 3072:
                            embeddings_list = [self._normalize_embedding(emb) for emb in embeddings_list]
                            logger.debug(f"Normalized {len(embeddings_list)} embeddings to unit norm")
                            
                        return embeddings_list[0] if len(embeddings_list) == 1 and isinstance(text, str) else embeddings_list
                    else:
                        logger.error(f"Unexpected response from Gemini API: {result}")
                        attempts += 1
                        self._rotate_api_key()
                else:
                    logger.error(f"Gemini API error: {response.status_code} - {response.text}")
                    attempts += 1
                    
                    if response.status_code == 429 or "quota exceeded" in response.text.lower() or "rate limit" in response.text.lower():
                        logger.warning(f"Rate limit reached for key {self.current_key_index + 1}, rotating keys")
                        rotated = self._rotate_api_key()
                        if not rotated:
                            logger.error("All API keys may be rate limited")
                            break
                    elif attempts >= max_attempts:
                        break
                        
                    time.sleep(1)
                
            except Exception as e:
                attempts += 1
                logger.error(f"Error generating embedding (attempt {attempts}): {e}")
                
                if attempts >= max_attempts:
                    break
                    
                self._rotate_api_key()
                time.sleep(1)
        
        total_time = time.time() - start_time
        logger.error(f"Failed to generate embedding after {max_attempts} attempts and {total_time:.2f}s")
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
        """Generate embeddings for multiple texts concurrently with API key rotation"""
        if not texts:
            logger.warning("No texts provided for batch embedding generation")
            return []
            
        if not self.api_keys:
            logger.error("No API keys available for batch embedding generation")
            return [None] * len(texts)
        
        start_time = time.time()
        logger.info(f"Starting batch embedding generation for {len(texts)} texts using {max_workers} workers and {len(self.api_keys)} API keys")
        
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