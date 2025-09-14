"""
Real Event Planning Service that integrates with the AI pipeline
"""
import asyncio
import uuid
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from pymongo.database import Database
from bson import ObjectId

from event_models import (
    EventFormData, EventPlanResponse, EventPlanSummary, 
    VendorRecommendation, TimelineItem, BudgetBreakdown,
    Task, TaskCreate, TaskUpdate, Vendor, VendorCreate, VendorUpdate,
    Guest, GuestCreate, GuestUpdate, BudgetSummary, BudgetItem,
    BudgetItemCreate, BudgetItemUpdate
)

# Import AI pipeline functions
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

try:
    from main import (
        llm_vendor_type, 
        generate_vendor_search_queries, 
        places_api_call, 
        semantic_match,
        generate_event_plan as generate_ai_plan
    )
    from db.place_embeddings_store import store_places_to_tidb
    AI_AVAILABLE = True
except ImportError as e:
    logger.warning(f"AI pipeline not available: {e}")
    AI_AVAILABLE = False

logger = logging.getLogger(__name__)

class EventService:
    def __init__(self, db: Database):
        self.db = db
        
    def _serialize_object_id(self, obj):
        """Convert ObjectId to string for JSON serialization"""
        if isinstance(obj, ObjectId):
            return str(obj)
        elif isinstance(obj, dict):
            return {k: self._serialize_object_id(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._serialize_object_id(item) for item in obj]
        return obj

    async def generate_event_plan(self, form_data: EventFormData, user_id: str) -> EventPlanResponse:
        """Generate a real event plan using AI pipeline"""
        try:
            logger.info(f"Generating event plan for user {user_id}")
            
            vendors = []
            ai_plan_text = f"Event plan for {form_data.eventType} - {form_data.description}"
            vendor_categories = {"event_type": form_data.eventType, "vendors": []}
            search_queries = []
            
            if AI_AVAILABLE:
                try:
                    # Step 1: Analyze vendor types using AI
                    logger.info("Analyzing vendor types with AI...")
                    vendor_categories = llm_vendor_type(form_data.description)
                    
                    if vendor_categories:
                        # Step 2: Generate search queries
                        logger.info("Generating search queries...")
                        search_queries = generate_vendor_search_queries(vendor_categories)
                        
                        if search_queries:
                            # Step 3: Search for places using Google Places API
                            logger.info(f"Searching places in {form_data.location}...")
                            places_results = places_api_call(search_queries, form_data.location)
                            
                            if places_results:
                                # Step 4: Store places in TiDB and perform semantic matching
                                logger.info("Storing places in TiDB...")
                                successful, failed = store_places_to_tidb(places_results)
                                logger.info(f"Stored {successful} places, {failed} failed")
                                
                                # Perform semantic matching
                                logger.info("Performing semantic matching...")
                                semantic_results = semantic_match(form_data.description, places_results, limit=6)
                                
                                # Convert places to vendor recommendations
                                vendors = self._convert_places_to_vendors(places_results, semantic_results)
                                
                                # Step 5: Generate comprehensive event plan using AI
                                logger.info("Generating AI event plan...")
                                ai_plan_text = generate_ai_plan(semantic_results, places_results, form_data.description)
                            else:
                                logger.warning("No places found from API")
                        else:
                            logger.warning("Failed to generate search queries")
                    else:
                        logger.warning("Failed to analyze vendor types")
                except Exception as ai_error:
                    logger.error(f"AI pipeline error: {ai_error}")
                    # Continue with fallback data
            else:
                logger.info("AI not available")
            
            # Step 6: Create structured event plan
            event_id = str(ObjectId())
            
            # Generate timeline based on event type
            timeline = self._generate_timeline(form_data.eventType, form_data.date)
            
            # Generate budget breakdown
            budget_breakdown = self._generate_budget_breakdown(form_data.eventType, form_data.budget)
            
            # Generate tips and checklist
            tips = self._generate_tips(form_data.eventType)
            checklist = self._generate_checklist(form_data.eventType)
            
            # Create event plan
            event_plan = EventPlanResponse(
                id=event_id,
                title=self._generate_event_title(form_data),
                eventType=form_data.eventType,
                description=form_data.description,
                location=form_data.location,
                date=form_data.date,
                budget=form_data.budget,
                guestCount=form_data.guestCount,
                duration=form_data.duration,
                vendors=vendors,
                timeline=timeline,
                budgetBreakdown=budget_breakdown,
                tips=tips,
                checklist=checklist,
                createdAt=datetime.now().isoformat(),
                updatedAt=datetime.now().isoformat()
            )
            
            # Store in MongoDB
            event_doc = {
                "_id": ObjectId(event_id),
                "user_id": ObjectId(user_id),
                "title": event_plan.title,
                "event_type": event_plan.eventType,
                "description": event_plan.description,
                "location": event_plan.location,
                "date": event_plan.date,
                "budget": event_plan.budget,
                "guest_count": event_plan.guestCount,
                "duration": event_plan.duration,
                "vendors": [v.dict() for v in event_plan.vendors],
                "timeline": [t.dict() for t in event_plan.timeline],
                "budget_breakdown": [b.dict() for b in event_plan.budgetBreakdown],
                "tips": event_plan.tips,
                "checklist": event_plan.checklist,
                "ai_plan_text": ai_plan_text,
                "vendor_categories": vendor_categories,
                "search_queries": search_queries,
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
            
            result = self.db.events.insert_one(event_doc)
            logger.info(f"Event plan stored with ID: {result.inserted_id}")
            
            return event_plan
            
        except Exception as e:
            logger.error(f"Error generating event plan: {e}", exc_info=True)
            raise Exception(f"Failed to generate event plan: {str(e)}")

    async def get_event_plans(self, user_id: str) -> List[EventPlanSummary]:
        """Get all event plans for a user"""
        try:
            events = list(self.db.events.find({"user_id": ObjectId(user_id)}))
            
            summaries = []
            for event in events:
                try:
                    event_date = datetime.fromisoformat(event["date"].replace('Z', '+00:00'))
                    status = self._calculate_status(event_date)
                    progress = self._calculate_progress(event["created_at"], event_date)
                    
                    summary = EventPlanSummary(
                        id=str(event["_id"]),
                        title=event["title"],
                        type=event["event_type"],
                        date=event["date"],
                        budget=event["budget"],
                        guests=int(event["guest_count"]) if event["guest_count"].isdigit() else 0,
                        status=status,
                        progress=progress,
                        createdAt=event["created_at"].isoformat()
                    )
                    summaries.append(summary)
                except Exception as e:
                    logger.error(f"Error processing event {event.get('_id')}: {e}")
                    continue
            
            return summaries
            
        except Exception as e:
            logger.error(f"Error fetching event plans: {e}")
            return []

    async def get_event_plan(self, event_id: str, user_id: str) -> Optional[EventPlanResponse]:
        """Get a specific event plan"""
        try:
            event = self.db.events.find_one({
                "_id": ObjectId(event_id),
                "user_id": ObjectId(user_id)
            })
            
            if not event:
                return None
            
            # Convert to EventPlanResponse
            vendors = [VendorRecommendation(**v) for v in event.get("vendors", [])]
            timeline = [TimelineItem(**t) for t in event.get("timeline", [])]
            budget_breakdown = [BudgetBreakdown(**b) for b in event.get("budget_breakdown", [])]
            
            return EventPlanResponse(
                id=str(event["_id"]),
                title=event["title"],
                eventType=event["event_type"],
                description=event["description"],
                location=event["location"],
                date=event["date"],
                budget=event["budget"],
                guestCount=event["guest_count"],
                duration=event["duration"],
                vendors=vendors,
                timeline=timeline,
                budgetBreakdown=budget_breakdown,
                tips=event.get("tips", []),
                checklist=event.get("checklist", []),
                createdAt=event["created_at"].isoformat(),
                updatedAt=event["updated_at"].isoformat()
            )
            
        except Exception as e:
            logger.error(f"Error fetching event plan {event_id}: {e}")
            return None

    async def update_event_plan(self, event_id: str, user_id: str, updates: dict) -> Optional[EventPlanResponse]:
        """Update an event plan"""
        try:
            # Update the event
            updates["updated_at"] = datetime.now()
            
            result = self.db.events.update_one(
                {"_id": ObjectId(event_id), "user_id": ObjectId(user_id)},
                {"$set": updates}
            )
            
            if result.matched_count == 0:
                return None
            
            # Return updated event
            return await self.get_event_plan(event_id, user_id)
            
        except Exception as e:
            logger.error(f"Error updating event plan {event_id}: {e}")
            return None

    async def delete_event_plan(self, event_id: str, user_id: str) -> bool:
        """Delete an event plan"""
        try:
            result = self.db.events.delete_one({
                "_id": ObjectId(event_id),
                "user_id": ObjectId(user_id)
            })
            
            return result.deleted_count > 0
            
        except Exception as e:
            logger.error(f"Error deleting event plan {event_id}: {e}")
            return False

    def _generate_fallback_vendors(self, event_type: str) -> List[VendorRecommendation]:
        """Generate fallback vendors when AI is not available"""
        fallback_vendors = {
            'wedding': [
                VendorRecommendation(
                    id="v1", name="Elegant Gardens Venue", category="venue", rating=4.8, price="$$$",
                    address="123 Garden Lane, City Center", phone="(555) 123-4567",
                    website="https://elegantgardens.com",
                    description="Beautiful outdoor venue with manicured gardens"
                ),
                VendorRecommendation(
                    id="v2", name="Gourmet Catering Co.", category="catering", rating=4.7, price="$$",
                    address="789 Chef Avenue", phone="(555) 345-6789",
                    website="https://gourmetcatering.com",
                    description="Premium catering service with customizable menus"
                )
            ],
            'birthday': [
                VendorRecommendation(
                    id="v3", name="Party Palace", category="venue", rating=4.6, price="$$",
                    address="456 Party Street", phone="(555) 234-5678",
                    website="https://partypalace.com",
                    description="Fun venue perfect for birthday celebrations"
                ),
                VendorRecommendation(
                    id="v4", name="Sweet Treats Bakery", category="catering", rating=4.8, price="$",
                    address="321 Cake Avenue", phone="(555) 456-7890",
                    website="https://sweettreats.com",
                    description="Custom cakes and party treats"
                )
            ]
        }
        
        event_key = event_type.lower().replace(' ', '')
        return fallback_vendors.get(event_key, fallback_vendors['birthday'])

    def _convert_places_to_vendors(self, places_results: List[dict], semantic_results: Dict[str, List[str]]) -> List[VendorRecommendation]:
        """Convert Google Places results to vendor recommendations"""
        vendors = []
        place_lookup = {place.get("place_id"): place for place in places_results}
        
        vendor_id_counter = 1
        
        for vendor_type, place_ids in semantic_results.items():
            for place_id in place_ids[:2]:  # Top 2 per category
                place = place_lookup.get(place_id)
                if place:
                    vendor = VendorRecommendation(
                        id=f"v{vendor_id_counter}",
                        name=place.get("displayName", {}).get("text", "Unknown Vendor"),
                        category=vendor_type,
                        rating=place.get("rating", 0.0),
                        price=self._get_price_level(place.get("priceLevel")),
                        address=place.get("formattedAddress", "Address not available"),
                        phone=place.get("nationalPhoneNumber", "Phone not available"),
                        website=place.get("websiteUri", "Website not available"),
                        description=place.get("editorialSummary", {}).get("text", "No description available")
                    )
                    vendors.append(vendor)
                    vendor_id_counter += 1
        
        return vendors

    def _get_price_level(self, price_level: Optional[str]) -> str:
        """Convert Google Places price level to readable format"""
        if not price_level:
            return "$"
        
        price_map = {
            "PRICE_LEVEL_FREE": "Free",
            "PRICE_LEVEL_INEXPENSIVE": "$",
            "PRICE_LEVEL_MODERATE": "$$",
            "PRICE_LEVEL_EXPENSIVE": "$$$",
            "PRICE_LEVEL_VERY_EXPENSIVE": "$$$$"
        }
        
        return price_map.get(price_level, "$")

    def _generate_timeline(self, event_type: str, event_date: str) -> List[TimelineItem]:
        """Generate timeline based on event type"""
        timeline_templates = {
            'wedding': [
                {'months': 6, 'task': 'Book venue and send save-the-dates', 'status': 'priority'},
                {'months': 4, 'task': 'Finalize catering and photography', 'status': 'upcoming'},
                {'months': 3, 'task': 'Send formal invitations', 'status': 'upcoming'},
                {'months': 2, 'task': 'Confirm all vendors', 'status': 'upcoming'},
                {'months': 1, 'task': 'Final headcount and details', 'status': 'upcoming'},
                {'weeks': 1, 'task': 'Final rehearsal and setup', 'status': 'upcoming'}
            ],
            'birthday': [
                {'months': 1, 'task': 'Plan theme and guest list', 'status': 'priority'},
                {'weeks': 3, 'task': 'Send invitations', 'status': 'upcoming'},
                {'weeks': 2, 'task': 'Order decorations and cake', 'status': 'upcoming'},
                {'weeks': 1, 'task': 'Confirm RSVPs and finalize details', 'status': 'upcoming'},
                {'days': 2, 'task': 'Prepare venue and decorations', 'status': 'upcoming'}
            ],
            'corporate': [
                {'months': 3, 'task': 'Secure venue and set agenda', 'status': 'priority'},
                {'months': 2, 'task': 'Arrange catering and AV equipment', 'status': 'upcoming'},
                {'weeks': 6, 'task': 'Send invitations to attendees', 'status': 'upcoming'},
                {'months': 1, 'task': 'Confirm speakers and presentations', 'status': 'upcoming'},
                {'weeks': 1, 'task': 'Final headcount and logistics', 'status': 'upcoming'}
            ]
        }
        
        event_type_key = event_type.lower().replace(' ', '')
        template = timeline_templates.get(event_type_key, timeline_templates['birthday'])
        
        timeline = []
        for i, item in enumerate(template):
            if 'months' in item:
                time_desc = f"{item['months']} month{'s' if item['months'] > 1 else ''} before"
            elif 'weeks' in item:
                time_desc = f"{item['weeks']} week{'s' if item['weeks'] > 1 else ''} before"
            else:
                time_desc = f"{item['days']} day{'s' if item['days'] > 1 else ''} before"
            
            timeline_item = TimelineItem(
                id=f"timeline_{i}",
                time=time_desc,
                task=item['task'],
                status=item['status'],
                description=item['task'],
                deadline=time_desc
            )
            timeline.append(timeline_item)
        
        return timeline

    def _generate_budget_breakdown(self, event_type: str, budget_str: str) -> List[BudgetBreakdown]:
        """Generate budget breakdown based on event type"""
        budget_templates = {
            'wedding': [
                {'category': 'Venue', 'percentage': 40},
                {'category': 'Catering', 'percentage': 30},
                {'category': 'Photography', 'percentage': 10},
                {'category': 'Flowers & Decorations', 'percentage': 8},
                {'category': 'Entertainment', 'percentage': 7},
                {'category': 'Miscellaneous', 'percentage': 5}
            ],
            'birthday': [
                {'category': 'Venue', 'percentage': 35},
                {'category': 'Catering', 'percentage': 30},
                {'category': 'Decorations', 'percentage': 20},
                {'category': 'Entertainment', 'percentage': 10},
                {'category': 'Miscellaneous', 'percentage': 5}
            ],
            'corporate': [
                {'category': 'Venue', 'percentage': 35},
                {'category': 'Catering', 'percentage': 25},
                {'category': 'AV Equipment', 'percentage': 15},
                {'category': 'Speakers/Presenters', 'percentage': 15},
                {'category': 'Materials', 'percentage': 5},
                {'category': 'Miscellaneous', 'percentage': 5}
            ]
        }
        
        event_type_key = event_type.lower().replace(' ', '')
        template = budget_templates.get(event_type_key, budget_templates['birthday'])
        
        # Extract budget amount
        total_budget = 10000  # Default
        try:
            total_budget = int(''.join(filter(str.isdigit, budget_str))) if budget_str else 10000
        except:
            pass
        
        breakdown = []
        for item in template:
            amount = round((total_budget * item['percentage']) / 100)
            breakdown.append(BudgetBreakdown(
                category=item['category'],
                amount=amount,
                percentage=item['percentage'],
                description=f"Budget allocation for {item['category'].lower()}"
            ))
        
        return breakdown

    def _generate_tips(self, event_type: str) -> List[str]:
        """Generate tips based on event type"""
        tips_map = {
            'wedding': [
                'Book your venue at least 6 months in advance',
                'Consider a weekday wedding to save costs',
                'Create a detailed timeline for vendors',
                'Have a backup plan for outdoor ceremonies',
                'Delegate tasks to reduce stress'
            ],
            'birthday': [
                'Send invitations 2-3 weeks in advance',
                'Consider dietary restrictions when planning',
                'Have backup indoor activities',
                'Delegate tasks to friends and family',
                'Take lots of photos'
            ],
            'corporate': [
                'Test all AV equipment beforehand',
                'Provide clear signage and directions',
                'Have registration ready with name badges',
                'Plan networking breaks',
                'Follow up with attendees after'
            ]
        }
        
        event_type_key = event_type.lower().replace(' ', '')
        return tips_map.get(event_type_key, tips_map['birthday'])

    def _generate_checklist(self, event_type: str) -> List[str]:
        """Generate checklist based on event type"""
        checklist_map = {
            'wedding': [
                'Venue booked and contract signed',
                'Catering menu finalized',
                'Photographer confirmed',
                'Invitations sent and RSVPs tracked',
                'Marriage license obtained',
                'Rehearsal dinner planned'
            ],
            'birthday': [
                'Guest list finalized',
                'Invitations sent',
                'Venue decorated',
                'Food and cake ordered',
                'Entertainment arranged',
                'Party favors prepared'
            ],
            'corporate': [
                'Venue set up properly',
                'AV equipment tested',
                'Catering confirmed',
                'Speakers briefed',
                'Registration area prepared',
                'Materials printed'
            ]
        }
        
        event_type_key = event_type.lower().replace(' ', '')
        return checklist_map.get(event_type_key, checklist_map['birthday'])

    def _generate_event_title(self, form_data: EventFormData) -> str:
        """Generate an event title"""
        try:
            date = datetime.fromisoformat(form_data.date.replace('Z', '+00:00'))
            month_year = date.strftime('%B %Y')
        except:
            month_year = 'TBD'
        
        return f"{form_data.eventType} - {month_year}"

    def _calculate_status(self, event_date: datetime) -> str:
        """Calculate event status"""
        now = datetime.now()
        days_until_event = (event_date - now).days
        
        if days_until_event < 0:
            return 'Completed'
        elif days_until_event <= 7:
            return 'This Week'
        elif days_until_event <= 30:
            return 'This Month'
        else:
            return 'Planning'

    def _calculate_progress(self, created_date: datetime, event_date: datetime) -> int:
        """Calculate event progress"""
        now = datetime.now()
        total_time = (event_date - created_date).total_seconds()
        elapsed_time = (now - created_date).total_seconds()
        
        if total_time <= 0:
            return 100
            
        progress = max(0, min(100, (elapsed_time / total_time) * 100))
        return round(progress)

# Global instance
event_service = None

def get_event_service(db: Database) -> EventService:
    """Get or create real event service instance"""
    global event_service
    if event_service is None:
        event_service = EventService(db)
    return event_service