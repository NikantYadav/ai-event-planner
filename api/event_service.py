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

from api.event_models import (
    EventFormData, EventPlanResponse, EventPlanSummary, 
    VendorRecommendation, TimelineItem, BudgetBreakdown,
    Task, TaskCreate, TaskUpdate, Vendor, VendorCreate, VendorUpdate,
    Guest, GuestCreate, GuestUpdate, BudgetSummary, BudgetItem,
    BudgetItemCreate, BudgetItemUpdate
)

from utils.logger import get_logger
logger = get_logger(__name__)

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
            logger.info(f"Starting event plan generation for user {user_id}")
            logger.info(f"Event type: {form_data.eventType}, Location: {form_data.location}")
            
            vendors = []
            ai_plan_text = f"Event plan for {form_data.eventType} - {form_data.description}"
            vendor_categories = {"event_type": form_data.eventType, "vendors": []}
            search_queries = []
            
            if AI_AVAILABLE:
                try:
                    # Extract API keys if provided
                    api_keys = form_data.geminiApiKeys if hasattr(form_data, 'geminiApiKeys') else None
                    if api_keys:
                        logger.info(f"Using {len(api_keys)} user-provided API keys")
                    
                    # Step 1: Analyze vendor types using AI
                    logger.info("Step 1/5: Analyzing vendor types with AI...")
                    vendor_categories = llm_vendor_type(form_data.description)
                    logger.info(f"Vendor analysis complete. Found categories: {list(vendor_categories.get('vendors', []))}")
                    
                    if vendor_categories:
                        # Step 2: Generate search queries
                        logger.info("Step 2/5: Generating search queries...")
                        search_queries = generate_vendor_search_queries(vendor_categories)
                        logger.info(f"Generated {len(search_queries) if search_queries else 0} search queries")
                        
                        if search_queries:
                            # Step 3: Search for places using Google Places API
                            logger.info(f"Step 3/5: Searching places in {form_data.location}...")
                            places_results = places_api_call(search_queries, form_data.location)
                            logger.info(f"Found {len(places_results) if places_results else 0} places")
                            
                            if places_results:
                                # Step 4: Store places in TiDB and perform semantic matching
                                logger.info("Step 4/5: Storing places in TiDB and performing semantic matching...")
                                successful, failed = store_places_to_tidb(places_results, api_keys=api_keys)
                                logger.info(f"Stored {successful} places, {failed} failed")
                                
                                # Perform semantic matching
                                logger.info("🎯 Performing semantic matching...")
                                semantic_results = semantic_match(form_data.description, places_results, limit=6, api_keys=api_keys)
                                logger.info(f"Semantic matching complete. Selected {len(semantic_results) if semantic_results else 0} top matches")

                                # Convert places to vendor recommendations
                                vendors = self._convert_places_to_vendors(places_results, semantic_results)
                                
                                # Step 5: Generate comprehensive event plan using AI
                                logger.info("Step 5/5: Generating comprehensive AI event plan...")
                                ai_plan_text = generate_ai_plan(semantic_results, places_results, form_data.description)
                                logger.info("AI event plan generation complete")
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
                logger.info("AI not available, using fallback data")
            
            # Step 6: Create structured event plan
            logger.info("Creating structured event plan...")
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
            logger.info(f"Event plan generation completed successfully for user {user_id}")
            
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

    # Task Management Methods
    async def get_event_tasks(self, event_id: str, user_id: str) -> List[Task]:
        """Get all tasks for a specific event"""
        try:
            tasks = list(self.db.tasks.find({
                "event_id": ObjectId(event_id),
                "user_id": ObjectId(user_id)
            }))
            
            return [Task(
                id=str(task["_id"]),
                title=task.get("title", ""),
                description=task.get("description", ""),
                status=task.get("status", "pending"),
                priority=task.get("priority", "medium"),
                category=task.get("category", ""),
                deadline=task.get("deadline", ""),
                assignedTo=task.get("assigned_to", ""),
                createdAt=task.get("created_at", datetime.now().isoformat()),
                updatedAt=task.get("updated_at", datetime.now().isoformat())
            ) for task in tasks]
            
        except Exception as e:
            logger.error(f"Error fetching tasks for event {event_id}: {e}")
            return []

    async def create_event_task(self, event_id: str, user_id: str, task_data: TaskCreate) -> Task:
        """Create a new task for an event"""
        try:
            now = datetime.now().isoformat()
            task_doc = {
                "_id": ObjectId(),
                "event_id": ObjectId(event_id),
                "user_id": ObjectId(user_id),
                "title": task_data.title,
                "description": task_data.description,
                "status": task_data.status,
                "priority": task_data.priority,
                "category": task_data.category,
                "deadline": task_data.deadline,
                "assigned_to": task_data.assignedTo,
                "created_at": now,
                "updated_at": now
            }
            
            self.db.tasks.insert_one(task_doc)
            
            return Task(
                id=str(task_doc["_id"]),
                title=task_doc["title"],
                description=task_doc["description"],
                status=task_doc["status"],
                priority=task_doc["priority"],
                category=task_doc["category"],
                deadline=task_doc["deadline"],
                assignedTo=task_doc["assigned_to"],
                createdAt=task_doc["created_at"],
                updatedAt=task_doc["updated_at"]
            )
            
        except Exception as e:
            logger.error(f"Error creating task for event {event_id}: {e}")
            raise

    async def update_event_task(self, event_id: str, user_id: str, task_id: str, task_update: TaskUpdate) -> Optional[Task]:
        """Update a specific task"""
        try:
            update_data = {k: v for k, v in task_update.dict().items() if v is not None}
            if "assignedTo" in update_data:
                update_data["assigned_to"] = update_data.pop("assignedTo")
            update_data["updated_at"] = datetime.now().isoformat()
            
            result = self.db.tasks.update_one(
                {
                    "_id": ObjectId(task_id),
                    "event_id": ObjectId(event_id),
                    "user_id": ObjectId(user_id)
                },
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                task = self.db.tasks.find_one({"_id": ObjectId(task_id)})
                if task:
                    return Task(
                        id=str(task["_id"]),
                        title=task["title"],
                        description=task["description"],
                        status=task["status"],
                        priority=task["priority"],
                        category=task["category"],
                        deadline=task["deadline"],
                        assignedTo=task.get("assigned_to", ""),
                        createdAt=task["created_at"],
                        updatedAt=task["updated_at"]
                    )
            
            return None
            
        except Exception as e:
            logger.error(f"Error updating task {task_id}: {e}")
            return None

    async def delete_event_task(self, event_id: str, user_id: str, task_id: str) -> bool:
        """Delete a specific task"""
        try:
            result = self.db.tasks.delete_one({
                "_id": ObjectId(task_id),
                "event_id": ObjectId(event_id),
                "user_id": ObjectId(user_id)
            })
            
            return result.deleted_count > 0
            
        except Exception as e:
            logger.error(f"Error deleting task {task_id}: {e}")
            return False

    # Vendor Management Methods
    async def get_event_vendors(self, event_id: str, user_id: str) -> List[Vendor]:
        """Get all vendors for a specific event"""
        try:
            vendors = list(self.db.vendors.find({
                "event_id": ObjectId(event_id),
                "user_id": ObjectId(user_id)
            }))
            
            return [Vendor(
                id=str(vendor["_id"]),
                name=vendor.get("name", ""),
                category=vendor.get("category", ""),
                contactPerson=vendor.get("contact_person", ""),
                email=vendor.get("email", ""),
                phone=vendor.get("phone", ""),
                address=vendor.get("address", ""),
                website=vendor.get("website", ""),
                rating=vendor.get("rating", 0.0),
                priceRange=vendor.get("price_range", ""),
                description=vendor.get("description", ""),
                services=vendor.get("services", []),
                availability=vendor.get("availability", ""),
                contractStatus=vendor.get("contract_status", "not_contacted"),
                quotedPrice=vendor.get("quoted_price", ""),
                finalPrice=vendor.get("final_price", ""),
                notes=vendor.get("notes", ""),
                createdAt=vendor.get("created_at", datetime.now().isoformat()),
                updatedAt=vendor.get("updated_at", datetime.now().isoformat())
            ) for vendor in vendors]
            
        except Exception as e:
            logger.error(f"Error fetching vendors for event {event_id}: {e}")
            return []

    async def create_event_vendor(self, event_id: str, user_id: str, vendor_data: VendorCreate) -> Vendor:
        """Create a new vendor for an event"""
        try:
            now = datetime.now().isoformat()
            vendor_doc = {
                "_id": ObjectId(),
                "event_id": ObjectId(event_id),
                "user_id": ObjectId(user_id),
                "name": vendor_data.name,
                "category": vendor_data.category,
                "contact_person": vendor_data.contactPerson,
                "email": vendor_data.email,
                "phone": vendor_data.phone,
                "address": vendor_data.address,
                "website": vendor_data.website,
                "rating": vendor_data.rating,
                "price_range": vendor_data.priceRange,
                "description": vendor_data.description,
                "services": vendor_data.services,
                "availability": vendor_data.availability,
                "contract_status": vendor_data.contractStatus,
                "quoted_price": vendor_data.quotedPrice,
                "final_price": vendor_data.finalPrice,
                "notes": vendor_data.notes,
                "created_at": now,
                "updated_at": now
            }
            
            self.db.vendors.insert_one(vendor_doc)
            
            return Vendor(
                id=str(vendor_doc["_id"]),
                name=vendor_doc["name"],
                category=vendor_doc["category"],
                contactPerson=vendor_doc["contact_person"],
                email=vendor_doc["email"],
                phone=vendor_doc["phone"],
                address=vendor_doc["address"],
                website=vendor_doc["website"],
                rating=vendor_doc["rating"],
                priceRange=vendor_doc["price_range"],
                description=vendor_doc["description"],
                services=vendor_doc["services"],
                availability=vendor_doc["availability"],
                contractStatus=vendor_doc["contract_status"],
                quotedPrice=vendor_doc["quoted_price"],
                finalPrice=vendor_doc["final_price"],
                notes=vendor_doc["notes"],
                createdAt=vendor_doc["created_at"],
                updatedAt=vendor_doc["updated_at"]
            )
            
        except Exception as e:
            logger.error(f"Error creating vendor for event {event_id}: {e}")
            raise

    async def update_event_vendor(self, event_id: str, user_id: str, vendor_id: str, vendor_update: VendorUpdate) -> Optional[Vendor]:
        """Update a specific vendor"""
        try:
            update_data = {k: v for k, v in vendor_update.dict().items() if v is not None}
            # Convert camelCase to snake_case for database fields
            field_mapping = {
                "contactPerson": "contact_person",
                "priceRange": "price_range",
                "contractStatus": "contract_status",
                "quotedPrice": "quoted_price",
                "finalPrice": "final_price"
            }
            
            for old_key, new_key in field_mapping.items():
                if old_key in update_data:
                    update_data[new_key] = update_data.pop(old_key)
            
            update_data["updated_at"] = datetime.now().isoformat()
            
            result = self.db.vendors.update_one(
                {
                    "_id": ObjectId(vendor_id),
                    "event_id": ObjectId(event_id),
                    "user_id": ObjectId(user_id)
                },
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                vendor = self.db.vendors.find_one({"_id": ObjectId(vendor_id)})
                if vendor:
                    return Vendor(
                        id=str(vendor["_id"]),
                        name=vendor["name"],
                        category=vendor["category"],
                        contactPerson=vendor.get("contact_person", ""),
                        email=vendor["email"],
                        phone=vendor["phone"],
                        address=vendor["address"],
                        website=vendor.get("website", ""),
                        rating=vendor["rating"],
                        priceRange=vendor["price_range"],
                        description=vendor["description"],
                        services=vendor["services"],
                        availability=vendor["availability"],
                        contractStatus=vendor["contract_status"],
                        quotedPrice=vendor.get("quoted_price", ""),
                        finalPrice=vendor.get("final_price", ""),
                        notes=vendor.get("notes", ""),
                        createdAt=vendor["created_at"],
                        updatedAt=vendor["updated_at"]
                    )
            
            return None
            
        except Exception as e:
            logger.error(f"Error updating vendor {vendor_id}: {e}")
            return None

    async def delete_event_vendor(self, event_id: str, user_id: str, vendor_id: str) -> bool:
        """Delete a specific vendor"""
        try:
            result = self.db.vendors.delete_one({
                "_id": ObjectId(vendor_id),
                "event_id": ObjectId(event_id),
                "user_id": ObjectId(user_id)
            })
            
            return result.deleted_count > 0
            
        except Exception as e:
            logger.error(f"Error deleting vendor {vendor_id}: {e}")
            return False

    # Guest Management Methods
    async def get_event_guests(self, event_id: str, user_id: str) -> List[Guest]:
        """Get all guests for a specific event"""
        try:
            guests = list(self.db.guests.find({
                "event_id": ObjectId(event_id),
                "user_id": ObjectId(user_id)
            }))
            
            return [Guest(
                id=str(guest["_id"]),
                name=guest.get("name", ""),
                email=guest.get("email", ""),
                phone=guest.get("phone", ""),
                rsvpStatus=guest.get("rsvp_status", "pending"),
                dietaryRestrictions=guest.get("dietary_restrictions", ""),
                plusOne=guest.get("plus_one", False),
                plusOneName=guest.get("plus_one_name", ""),
                tableAssignment=guest.get("table_assignment", ""),
                specialRequests=guest.get("special_requests", ""),
                invitationSent=guest.get("invitation_sent", False),
                invitationSentDate=guest.get("invitation_sent_date", ""),
                rsvpDate=guest.get("rsvp_date", ""),
                createdAt=guest.get("created_at", datetime.now().isoformat()),
                updatedAt=guest.get("updated_at", datetime.now().isoformat())
            ) for guest in guests]
            
        except Exception as e:
            logger.error(f"Error fetching guests for event {event_id}: {e}")
            return []

    async def create_event_guest(self, event_id: str, user_id: str, guest_data: GuestCreate) -> Guest:
        """Create a new guest for an event"""
        try:
            now = datetime.now().isoformat()
            guest_doc = {
                "_id": ObjectId(),
                "event_id": ObjectId(event_id),
                "user_id": ObjectId(user_id),
                "name": guest_data.name,
                "email": guest_data.email,
                "phone": guest_data.phone,
                "rsvp_status": guest_data.rsvpStatus,
                "dietary_restrictions": guest_data.dietaryRestrictions,
                "plus_one": guest_data.plusOne,
                "plus_one_name": guest_data.plusOneName,
                "table_assignment": guest_data.tableAssignment,
                "special_requests": guest_data.specialRequests,
                "invitation_sent": guest_data.invitationSent,
                "invitation_sent_date": guest_data.invitationSentDate,
                "rsvp_date": guest_data.rsvpDate,
                "created_at": now,
                "updated_at": now
            }
            
            self.db.guests.insert_one(guest_doc)
            
            return Guest(
                id=str(guest_doc["_id"]),
                name=guest_doc["name"],
                email=guest_doc["email"],
                phone=guest_doc["phone"],
                rsvpStatus=guest_doc["rsvp_status"],
                dietaryRestrictions=guest_doc["dietary_restrictions"],
                plusOne=guest_doc["plus_one"],
                plusOneName=guest_doc["plus_one_name"],
                tableAssignment=guest_doc["table_assignment"],
                specialRequests=guest_doc["special_requests"],
                invitationSent=guest_doc["invitation_sent"],
                invitationSentDate=guest_doc["invitation_sent_date"],
                rsvpDate=guest_doc["rsvp_date"],
                createdAt=guest_doc["created_at"],
                updatedAt=guest_doc["updated_at"]
            )
            
        except Exception as e:
            logger.error(f"Error creating guest for event {event_id}: {e}")
            raise

    async def update_event_guest(self, event_id: str, user_id: str, guest_id: str, guest_update: GuestUpdate) -> Optional[Guest]:
        """Update a specific guest"""
        try:
            update_data = {k: v for k, v in guest_update.dict().items() if v is not None}
            # Convert camelCase to snake_case for database fields
            field_mapping = {
                "rsvpStatus": "rsvp_status",
                "dietaryRestrictions": "dietary_restrictions",
                "plusOne": "plus_one",
                "plusOneName": "plus_one_name",
                "tableAssignment": "table_assignment",
                "specialRequests": "special_requests",
                "invitationSent": "invitation_sent",
                "invitationSentDate": "invitation_sent_date",
                "rsvpDate": "rsvp_date"
            }
            
            for old_key, new_key in field_mapping.items():
                if old_key in update_data:
                    update_data[new_key] = update_data.pop(old_key)
            
            update_data["updated_at"] = datetime.now().isoformat()
            
            result = self.db.guests.update_one(
                {
                    "_id": ObjectId(guest_id),
                    "event_id": ObjectId(event_id),
                    "user_id": ObjectId(user_id)
                },
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                guest = self.db.guests.find_one({"_id": ObjectId(guest_id)})
                if guest:
                    return Guest(
                        id=str(guest["_id"]),
                        name=guest["name"],
                        email=guest["email"],
                        phone=guest.get("phone", ""),
                        rsvpStatus=guest["rsvp_status"],
                        dietaryRestrictions=guest.get("dietary_restrictions", ""),
                        plusOne=guest["plus_one"],
                        plusOneName=guest.get("plus_one_name", ""),
                        tableAssignment=guest.get("table_assignment", ""),
                        specialRequests=guest.get("special_requests", ""),
                        invitationSent=guest["invitation_sent"],
                        invitationSentDate=guest.get("invitation_sent_date", ""),
                        rsvpDate=guest.get("rsvp_date", ""),
                        createdAt=guest["created_at"],
                        updatedAt=guest["updated_at"]
                    )
            
            return None
            
        except Exception as e:
            logger.error(f"Error updating guest {guest_id}: {e}")
            return None

    async def delete_event_guest(self, event_id: str, user_id: str, guest_id: str) -> bool:
        """Delete a specific guest"""
        try:
            result = self.db.guests.delete_one({
                "_id": ObjectId(guest_id),
                "event_id": ObjectId(event_id),
                "user_id": ObjectId(user_id)
            })
            
            return result.deleted_count > 0
            
        except Exception as e:
            logger.error(f"Error deleting guest {guest_id}: {e}")
            return False

    # Budget Management Methods
    async def get_event_budget(self, event_id: str, user_id: str) -> BudgetSummary:
        """Get budget summary for a specific event"""
        try:
            # Get budget items for this event
            budget_items = list(self.db.budget_items.find({
                "event_id": ObjectId(event_id),
                "user_id": ObjectId(user_id)
            }))
            
            # Convert to BudgetItem objects
            items = [BudgetItem(
                id=str(item["_id"]),
                category=item.get("category", ""),
                item=item.get("item", ""),
                estimatedCost=item.get("estimated_cost", 0.0),
                actualCost=item.get("actual_cost"),
                vendor=item.get("vendor", ""),
                status=item.get("status", "planned"),
                notes=item.get("notes", ""),
                createdAt=item.get("created_at", datetime.now().isoformat()),
                updatedAt=item.get("updated_at", datetime.now().isoformat())
            ) for item in budget_items]
            
            # Calculate totals
            total_estimated = sum(item.estimatedCost for item in items)
            total_spent = sum(item.actualCost or 0 for item in items)
            total_remaining = total_estimated - total_spent
            
            # Create category breakdown
            category_totals = {}
            for item in items:
                if item.category not in category_totals:
                    category_totals[item.category] = {"estimated": 0, "spent": 0}
                category_totals[item.category]["estimated"] += item.estimatedCost
                category_totals[item.category]["spent"] += item.actualCost or 0
            
            category_breakdown = []
            for category, totals in category_totals.items():
                percentage = round((totals["estimated"] / total_estimated) * 100) if total_estimated > 0 else 0
                category_breakdown.append(BudgetBreakdown(
                    category=category,
                    amount=int(totals["estimated"]),
                    percentage=percentage,
                    description=f"Budget allocation for {category.lower()}"
                ))
            
            return BudgetSummary(
                totalBudget=total_estimated,
                totalSpent=total_spent,
                totalRemaining=total_remaining,
                categoryBreakdown=category_breakdown,
                items=items
            )
            
        except Exception as e:
            logger.error(f"Error fetching budget for event {event_id}: {e}")
            return BudgetSummary(
                totalBudget=0.0,
                totalSpent=0.0,
                totalRemaining=0.0,
                categoryBreakdown=[],
                items=[]
            )

    async def create_budget_item(self, event_id: str, item_data: BudgetItemCreate, user_id: str) -> BudgetItem:
        """Create a new budget item for an event"""
        try:
            now = datetime.now().isoformat()
            item_doc = {
                "_id": ObjectId(),
                "event_id": ObjectId(event_id),
                "user_id": ObjectId(user_id),
                "category": item_data.category,
                "item": item_data.item,
                "estimated_cost": item_data.estimatedCost,
                "actual_cost": None,
                "vendor": item_data.vendor,
                "status": "planned",
                "notes": item_data.notes,
                "created_at": now,
                "updated_at": now
            }
            
            self.db.budget_items.insert_one(item_doc)
            
            return BudgetItem(
                id=str(item_doc["_id"]),
                category=item_doc["category"],
                item=item_doc["item"],
                estimatedCost=item_doc["estimated_cost"],
                actualCost=item_doc["actual_cost"],
                vendor=item_doc["vendor"],
                status=item_doc["status"],
                notes=item_doc["notes"],
                createdAt=item_doc["created_at"],
                updatedAt=item_doc["updated_at"]
            )
            
        except Exception as e:
            logger.error(f"Error creating budget item for event {event_id}: {e}")
            raise

    async def update_budget_item(self, event_id: str, item_id: str, item_update: BudgetItemUpdate, user_id: str) -> Optional[BudgetItem]:
        """Update a specific budget item"""
        try:
            update_data = {k: v for k, v in item_update.dict().items() if v is not None}
            # Convert camelCase to snake_case for database fields
            field_mapping = {
                "estimatedCost": "estimated_cost",
                "actualCost": "actual_cost"
            }
            
            for old_key, new_key in field_mapping.items():
                if old_key in update_data:
                    update_data[new_key] = update_data.pop(old_key)
            
            update_data["updated_at"] = datetime.now().isoformat()
            
            result = self.db.budget_items.update_one(
                {
                    "_id": ObjectId(item_id),
                    "event_id": ObjectId(event_id),
                    "user_id": ObjectId(user_id)
                },
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                item = self.db.budget_items.find_one({"_id": ObjectId(item_id)})
                if item:
                    return BudgetItem(
                        id=str(item["_id"]),
                        category=item["category"],
                        item=item["item"],
                        estimatedCost=item["estimated_cost"],
                        actualCost=item.get("actual_cost"),
                        vendor=item.get("vendor", ""),
                        status=item["status"],
                        notes=item.get("notes", ""),
                        createdAt=item["created_at"],
                        updatedAt=item["updated_at"]
                    )
            
            return None
            
        except Exception as e:
            logger.error(f"Error updating budget item {item_id}: {e}")
            return None

    async def delete_budget_item(self, event_id: str, item_id: str, user_id: str) -> bool:
        """Delete a specific budget item"""
        try:
            result = self.db.budget_items.delete_one({
                "_id": ObjectId(item_id),
                "event_id": ObjectId(event_id),
                "user_id": ObjectId(user_id)
            })
            
            return result.deleted_count > 0
            
        except Exception as e:
            logger.error(f"Error deleting budget item {item_id}: {e}")
            return False