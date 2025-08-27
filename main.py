import json 
import re
from typing import Dict, List, Any
from controllers.llm_calls import GeminiLLM
from utils.logger import get_logger

logger = get_logger(__name__)
def llm_vendor_type(user_event_description):
    """
    Analyze event description and return required vendor categories in JSON format
    """

    prompt = f"""You are an expert Event Planner. 
    Your task is to analyze the given event description and generate a comprehensive JSON list of vendor categories required for the successful execution of that event. 

    Rules:
    - Always return output STRICTLY in JSON.
    - The JSON must include "event_type" and a "vendors" array.
    - The "vendors" array should list all vendor categories relevant to the event.
    - Think broadly and include both common and uncommon vendors depending on the event requirements.

    User Input:
    "{user_event_description}"
    """
    
    try:
        llm = GeminiLLM()
        response = llm.generate(prompt, temperature=0.7)

        match = re.search(r"\{.*\}", response, re.DOTALL)
        if not match:
            raise GeminiLLMError("No valid JSON found in LLM response")

        json_str = match.group(0).strip()

        # Parse into dict
        parsed_json = json.loads(json_str)

        return parsed_json
        
    except Exception as e:
        logger.error(f"Error analyzing vendor types: {e}")
        return None



if __name__ == "__main__":
    user_event_description = """We’re launching a new eco-friendly skincare brand in New York City.
    Budget: $15,000.
    We want a trendy but affordable venue, maybe a rooftop or loft, for about 50–70 attendees including influencers and press.
    The theme should be natural and minimalist, with lots of greenery and neutral colors.
    We’ll need catering with healthy snacks and drinks, a photographer, and a space for product displays.
    The vibe should be Instagrammable and on-brand."""
    try:
        vendor_categories = llm_vendor_type(user_event_description)
        print(vendor_categories)
    except Exception as e:
        print(f"An error occurred: {e}")

