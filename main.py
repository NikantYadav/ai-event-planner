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
from src.services.event_planner import EventPlannerService
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
    """Main function with options for collecting vendors or planning events."""
    # Load environment variables
    load_dotenv()
    
    # Check required environment variables
    if not check_env_vars():
        return
    
    print("🎉 AI Event Planner")
    print("1. Collect decoration vendors (populate database)")
    print("2. Plan an event (find vendors for your event)")
    
    choice = input("\nSelect an option (1 or 2): ").strip()
    
    if choice == "1":
        collect_vendors()
    elif choice == "2":
        plan_event()
    else:
        print("❌ Invalid choice. Please select 1 or 2.")

def collect_vendors():
    """Collect decoration vendors with Gemini embeddings."""
    logger.info("🚀 Starting Gurugram Decoration Vendors Collection with Gemini embeddings...")
    
    # Create and run vendor collector service
    collector = VendorCollectorService()
    collector.collect_decoration_vendors()

def plan_event():
    """Plan an event and find relevant vendors."""
    logger.info("🎯 Starting Event Planning...")
    
    # Get event description from user
    print("\n🎪 Describe the type of event you want to organize:")
    print("(e.g., 'birthday party for 8-year-old with princess theme', 'corporate annual meeting for 100 people', 'outdoor wedding reception')")
    
    event_description = input("\nEvent description: ").strip()
    
    if not event_description:
        print("❌ Please provide an event description.")
        return
    
    # Create event planner service and plan the event
    planner = EventPlannerService()
    result = planner.plan_event(event_description)
    
    if "error" in result:
        print(f"❌ Error: {result['error']}")
        return
    
    # Display results
    print(f"\n🎯 Event: {result['event_description']}")
    print(f"🔍 Search Query: {result['search_query']}")
    print(f"📊 Found {result['total_found']} relevant vendors:\n")
    
    for i, vendor in enumerate(result['top_vendors'], 1):
        print(f"{i}. {vendor['name']}")
        print(f"   📍 {vendor['formatted_address']}")
        print(f"   ⭐ Rating: {vendor.get('rating', 'N/A')} ({vendor.get('user_rating_count', 0)} reviews)")
        print(f"   🎯 Similarity: {vendor['similarity_score']:.3f}")
        print(f"   🏷️ Type: {vendor.get('primary_type', 'N/A')}")
        print(f"   🎨 Specialties: {vendor.get('specialties', 'general decoration')}")
        
        if vendor.get('website_uri'):
            print(f"   🌐 Website: {vendor['website_uri']}")
        if vendor.get('national_phone'):
            print(f"   📞 Phone: {vendor['national_phone']}")
        if vendor.get('google_maps_uri'):
            print(f"   🗺️ Maps: {vendor['google_maps_uri']}")
        
        print()  # Empty line between vendors

if __name__ == "__main__":
    main()
