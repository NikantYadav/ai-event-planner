#!/usr/bin/env python3
"""
Simple CLI for Event Planning - Find vendors for your event
"""
import os
import sys
from dotenv import load_dotenv

# Make sure the src directory is in the path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.services.event_planner import EventPlannerService
from src.utils.logger import get_logger

logger = get_logger("event_planner_cli")

def check_env_vars():
    """Check required environment variables."""
    required_vars = ['GEMINI_API_KEY']
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        logger.error("Please create a .env file with the required variables.")
        return False
    
    return True

def main():
    """Main CLI function for event planning."""
    # Load environment variables
    load_dotenv()
    
    # Check required environment variables
    if not check_env_vars():
        return
    
    print("🎪 AI Event Planner - Find Perfect Vendors for Your Event!")
    print("=" * 55)
    
    if len(sys.argv) > 1:
        # Use command line argument as event description
        event_description = ' '.join(sys.argv[1:])
    else:
        # Interactive mode
        print("\nDescribe the type of event you want to organize:")
        print("Examples:")
        print("  • 'birthday party for 8-year-old with princess theme'")
        print("  • 'corporate annual meeting for 100 people'")
        print("  • 'outdoor wedding reception for 150 guests'")
        print("  • 'baby shower with floral decorations'")
        print()
        
        event_description = input("Event description: ").strip()
    
    if not event_description:
        print("❌ Please provide an event description.")
        return
    
    print(f"\n🔄 Processing your request...")
    
    # Create event planner service and plan the event
    try:
        planner = EventPlannerService()
        result = planner.plan_event(event_description)
        
        if "error" in result:
            print(f"❌ Error: {result['error']}")
            return
        
        # Display results
        print(f"\n🎯 Event: {result['event_description']}")
        print(f"🔍 Optimized Search: {result['search_query']}")
        print(f"📊 Found {result['total_found']} relevant vendors")
        print("=" * 55)
        
        for i, vendor in enumerate(result['top_vendors'], 1):
            print(f"\n{i}. 🏪 {vendor['name']}")
            print(f"   📍 {vendor['formatted_address']}")
            
            rating_str = f"{vendor.get('rating', 'N/A')}"
            if vendor.get('user_rating_count', 0) > 0:
                rating_str += f" ({vendor['user_rating_count']} reviews)"
            print(f"   ⭐ Rating: {rating_str}")
            
            print(f"   🎯 Match Score: {vendor['similarity_score']:.1%}")
            print(f"   🏷️ Type: {vendor.get('primary_type', 'N/A')}")
            print(f"   🎨 Specialties: {vendor.get('specialties', 'general decoration')}")
            
            contact_info = []
            if vendor.get('national_phone'):
                contact_info.append(f"📞 {vendor['national_phone']}")
            if vendor.get('website_uri'):
                contact_info.append(f"🌐 {vendor['website_uri']}")
            if vendor.get('google_maps_uri'):
                contact_info.append(f"🗺️ Maps")
            
            if contact_info:
                print(f"   {' | '.join(contact_info)}")
        
        print("\n" + "=" * 55)
        print("🎉 Happy Event Planning!")
        
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        print(f"❌ An error occurred: {e}")

if __name__ == "__main__":
    main()
