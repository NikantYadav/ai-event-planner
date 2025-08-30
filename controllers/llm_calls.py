import os
import logging
import google.generativeai as genai
from google.generativeai.types import GenerationConfig
from dotenv import load_dotenv
from utils.logger import get_logger
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Optional
import time
from utils.config import Config

load_dotenv()
GEMINI_MODEL = os.getenv('GEMINI_MODEL')
logger = get_logger(__name__)   

class GeminiLLM:
    def __init__(self):
        try:
            api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_AI_API_KEY")
            if not api_key:
                logger.error("API key required: set GEMINI_API_KEY environment variable")
                return

            genai.configure(api_key=api_key)
            model_name = GEMINI_MODEL if GEMINI_MODEL else "gemini-1.5-flash"
            self.model = genai.GenerativeModel(model_name)
            logger.info(f"Initialized Gemini LLM with model: {model_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Gemini LLM: {e}")
            
    def generate(self, prompt, temperature=None, max_tokens=None):
        """Generate content from prompt"""
        try:
            config = {}
            if temperature is not None:
                config['temperature'] = temperature
            if max_tokens is not None:
                config['max_output_tokens'] = max_tokens
            
            response = self.model.generate_content(
                prompt,
                generation_config=GenerationConfig(**config) if config else None
            )
            
            if not response.text:
                logger.error("No content generated - response was blocked or empty")
                return None
            return response.text
            
        except Exception as e:
            logger.error(f"Error generating content: {e}")
            return None
    
    def generate_batch(self, prompts: List[str], max_workers: int = 5) -> List[Optional[str]]:
        """Generate content for multiple prompts concurrently"""
        if not prompts:
            return []
        
        results = [None] * len(prompts)
        
        def generate_single(index: int, prompt: str) -> tuple:
            time.sleep(60 / Config.RPM)  # Simple rate limiting based on RPM
            result = self.generate(prompt)
            return (index, result)
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_index = {
                executor.submit(generate_single, i, prompt): i 
                for i, prompt in enumerate(prompts)
            }
            
            for future in as_completed(future_to_index):
                try:
                    index, result = future.result()
                    results[index] = result
                except Exception as e:
                    index = future_to_index[future]
                    logger.error(f"Error processing batch item {index}: {e}")
                    results[index] = None
        
        return results