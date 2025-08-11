#!/usr/bin/env python3
"""
Main entry point for the AI Event Planner application.
This script collects decoration vendors in Gurugram using Google Places API,
enriches them with Gemini embeddings, and saves to a database.
"""
import os
import sys
from dotenv import load_dotenv

# Make sure the src directory is in the path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.vendor_collector import VendorCollectorService
from src.utils.logger import get_logger

logger = get_logger("main")

def check_env_vars():
    """Check required environment variables."""
    required_vars = [
        'GOOGLE_MAPS_API_KEY',
        'GEMINI_API_KEY',
        'TIDB_HOST',
        'TIDB_USER',
        'TIDB_PASSWORD',
        'TIDB_DATABASE'
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        logger.error("Please create a .env file with the required variables.")
        return False
    
    return True

def main():
    """Main function to collect decoration vendors with Gemini embeddings."""
    # Load environment variables
    load_dotenv()
    
    # Check required environment variables
    if not check_env_vars():
        return
    
    logger.info("🚀 Starting Gurugram Decoration Vendors Collection with Gemini embeddings...")
    
    # Create and run vendor collector service
    collector = VendorCollectorService()
    collector.collect_decoration_vendors()

if __name__ == "__main__":
    main()
