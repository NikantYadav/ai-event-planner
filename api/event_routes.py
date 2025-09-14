from fastapi import APIRouter, HTTPException, Depends, Request
from typing import List
from pymongo.database import Database
from event_models import (
    EventFormData, EventPlanResponse, EventPlanSummary, EventPlanUpdate,
    Task, TaskCreate, TaskUpdate, Vendor, VendorCreate, VendorUpdate,
    Guest, GuestCreate, GuestUpdate, BudgetSummary, BudgetItem, 
    BudgetItemCreate, BudgetItemUpdate
)
from real_event_service import get_event_service
from routes import get_current_user
from mongo import get_db
import re
from datetime import datetime

# Create router for event planning endpoints
event_router = APIRouter(prefix="/api/events", tags=["events"])

def validate_event_input(form_data: EventFormData) -> EventFormData:
    """Validate and sanitize event form input data"""
    
    # Sanitize strings by stripping whitespace and removing potentially harmful characters
    def sanitize_string(value: str) -> str:
        if not value:
            return ""
        # Strip whitespace and remove any HTML-like tags
        sanitized = re.sub(r'<[^>]*>', '', str(value).strip())
        return sanitized
    
    # Validate required fields
    if not form_data.eventType or not sanitize_string(form_data.eventType):
        raise HTTPException(status_code=400, detail="Event type is required")
    
    if not form_data.description or not sanitize_string(form_data.description):
        raise HTTPException(status_code=400, detail="Event description is required")
    
    if not form_data.location or not sanitize_string(form_data.location):
        raise HTTPException(status_code=400, detail="Event location is required")
    
    if not form_data.date or not sanitize_string(form_data.date):
        raise HTTPException(status_code=400, detail="Event date is required")
 
    # Validate budget (should be numeric or contain numeric value)
    if form_data.budget:
        budget_str = sanitize_string(form_data.budget)
        # Extract numeric value from budget string
        budget_numbers = re.findall(r'\d+', budget_str)
        if not budget_numbers:
            raise HTTPException(status_code=400, detail="Budget must contain a numeric value")
    
    # Validate guest count (should be numeric)
    if form_data.guestCount:
        guest_str = sanitize_string(form_data.guestCount)
        guest_numbers = re.findall(r'\d+', guest_str)
        if not guest_numbers:
            raise HTTPException(status_code=400, detail="Guest count must contain a numeric value")
        
    
    # Create sanitized form data
    sanitized_data = EventFormData(
        eventType=sanitize_string(form_data.eventType),
        description=sanitize_string(form_data.description),
        location=sanitize_string(form_data.location),
        date=sanitize_string(form_data.date),
        budget=sanitize_string(form_data.budget) if form_data.budget else "",
        guestCount=sanitize_string(form_data.guestCount) if form_data.guestCount else "",
        duration=sanitize_string(form_data.duration) if form_data.duration else ""
    )
    
    return sanitized_data

@event_router.post("/generate", response_model=EventPlanResponse)
async def generate_event_plan(
    request: Request,
    form_data: EventFormData, 
    current_user=Depends(get_current_user),
    db: Database = Depends(get_db)
):
    """Generate a new event plan based on form data"""
    try:
        # Validate and sanitize input
        form_data = validate_event_input(form_data)
        
        service = get_event_service(db)
        event_plan = await service.generate_event_plan(form_data, str(current_user["_id"]))
        
        
        return event_plan
    except HTTPException:
        raise
    except Exception as e:
        # Log error
        raise HTTPException(status_code=500, detail=f"Failed to generate event plan: {str(e)}")

@event_router.get("/", response_model=List[EventPlanSummary])
async def get_event_plans(
    current_user=Depends(get_current_user),
    db: Database = Depends(get_db)
):
    """Get all event plans for the current user"""
    try:
        service = get_event_service(db)
        plans = await service.get_event_plans(str(current_user["_id"]))
        return plans
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch event plans: {str(e)}")

@event_router.get("/{event_id}", response_model=EventPlanResponse)
async def get_event_plan(
    event_id: str,
    current_user=Depends(get_current_user),
    db: Database = Depends(get_db)
):
    """Get a specific event plan by ID"""
    try:
        service = get_event_service(db)
        plan = await service.get_event_plan(event_id, str(current_user["_id"]))
        if not plan:
            raise HTTPException(status_code=404, detail="Event plan not found")
        return plan
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch event plan: {str(e)}")

@event_router.put("/{event_id}", response_model=EventPlanResponse)
async def update_event_plan(
    event_id: str, 
    updates: EventPlanUpdate,
    current_user=Depends(get_current_user),
    db: Database = Depends(get_db)
):
    """Update an existing event plan"""
    try:
        # Convert to dict and remove None values
        update_data = {k: v for k, v in updates.dict().items() if v is not None}
        
        service = get_event_service(db)
        updated_plan = await service.update_event_plan(event_id, str(current_user["_id"]), update_data)
        if not updated_plan:
            raise HTTPException(status_code=404, detail="Event plan not found")
        return updated_plan
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update event plan: {str(e)}")

@event_router.delete("/{event_id}")
async def delete_event_plan(
    event_id: str,
    current_user=Depends(get_current_user),
    db: Database = Depends(get_db)
):
    """Delete an event plan"""
    try:
        service = get_event_service(db)
        success = await service.delete_event_plan(event_id, str(current_user["_id"]))
        if not success:
            raise HTTPException(status_code=404, detail="Event plan not found")
        return {"message": "Event plan deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete event plan: {str(e)}")

# Task Management Endpoints
@event_router.get("/{event_id}/tasks", response_model=List[Task])
async def get_event_tasks(
    event_id: str,
    current_user=Depends(get_current_user),
    db: Database = Depends(get_db)
):
    """Get all tasks for a specific event"""
    try:
        service = get_event_service(db)
        tasks = await service.get_event_tasks(event_id, str(current_user["_id"]))
        return tasks
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch tasks: {str(e)}")

@event_router.post("/{event_id}/tasks", response_model=Task)
async def create_event_task(
    event_id: str, 
    task_data: TaskCreate,
    current_user=Depends(get_current_user),
    db: Database = Depends(get_db)
):
    """Create a new task for an event"""
    try:
        service = get_event_service(db)
        task = await service.create_event_task(event_id, str(current_user["_id"]), task_data)
        return task
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create task: {str(e)}")

@event_router.put("/{event_id}/tasks/{task_id}", response_model=Task)
async def update_event_task(
    event_id: str, 
    task_id: str, 
    task_update: TaskUpdate,
    current_user=Depends(get_current_user),
    db: Database = Depends(get_db)
):
    """Update a specific task"""
    try:
        service = get_event_service(db)
        task = await service.update_event_task(event_id, str(current_user["_id"]), task_id, task_update)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        return task
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update task: {str(e)}")

# Vendor Management Endpoints
@event_router.get("/{event_id}/vendors", response_model=List[Vendor])
async def get_event_vendors(
    event_id: str,
    current_user=Depends(get_current_user),
    db: Database = Depends(get_db)
):
    """Get all vendors for a specific event"""
    try:
        service = get_event_service(db)
        vendors = await service.get_event_vendors(event_id, str(current_user["_id"]))
        return vendors
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch vendors: {str(e)}")

@event_router.post("/{event_id}/vendors", response_model=Vendor)
async def create_event_vendor(
    event_id: str, 
    vendor_data: VendorCreate,
    current_user=Depends(get_current_user),
    db: Database = Depends(get_db)
):
    """Add a new vendor to an event"""
    try:
        service = get_event_service(db)
        vendor = await service.create_event_vendor(event_id, str(current_user["_id"]), vendor_data)
        return vendor
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create vendor: {str(e)}")

@event_router.put("/{event_id}/vendors/{vendor_id}", response_model=Vendor)
async def update_event_vendor(
    event_id: str, 
    vendor_id: str, 
    vendor_update: VendorUpdate,
    current_user=Depends(get_current_user),
    db: Database = Depends(get_db)
):
    """Update a specific vendor"""
    try:
        service = get_event_service(db)
        vendor = await service.update_event_vendor(event_id, str(current_user["_id"]), vendor_id, vendor_update)
        if not vendor:
            raise HTTPException(status_code=404, detail="Vendor not found")
        return vendor
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update vendor: {str(e)}")

# Guest & RSVP Management Endpoints
@event_router.get("/{event_id}/guests", response_model=List[Guest])
async def get_event_guests(
    event_id: str,
    current_user=Depends(get_current_user),
    db: Database = Depends(get_db)
):
    """Get all guests for a specific event"""
    try:
        service = get_event_service(db)
        guests = await service.get_event_guests(event_id, str(current_user["_id"]))
        return guests
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch guests: {str(e)}")

@event_router.post("/{event_id}/guests", response_model=Guest)
async def create_event_guest(
    event_id: str, 
    guest_data: GuestCreate,
    current_user=Depends(get_current_user),
    db: Database = Depends(get_db)
):
    """Add a new guest to an event"""
    try:
        service = get_event_service(db)
        guest = await service.create_event_guest(event_id, str(current_user["_id"]), guest_data)
        return guest
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create guest: {str(e)}")

@event_router.put("/{event_id}/guests/{guest_id}", response_model=Guest)
async def update_event_guest(
    event_id: str, 
    guest_id: str, 
    guest_update: GuestUpdate,
    current_user=Depends(get_current_user),
    db: Database = Depends(get_db)
):
    """Update a specific guest"""
    try:
        service = get_event_service(db)
        guest = await service.update_event_guest(event_id, str(current_user["_id"]), guest_id, guest_update)
        if not guest:
            raise HTTPException(status_code=404, detail="Guest not found")
        return guest
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update guest: {str(e)}")

# Budget Management Endpoints
@event_router.get("/{event_id}/budget", response_model=BudgetSummary)
async def get_event_budget(event_id: str):
    """Get budget summary for a specific event"""
    try:
        budget = await mock_event_api.get_event_budget(event_id)
        return budget
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch budget: {str(e)}")

@event_router.post("/{event_id}/budget/items", response_model=BudgetItem)
async def create_budget_item(event_id: str, item_data: BudgetItemCreate):
    """Add a new budget item to an event"""
    try:
        item = await mock_event_api.create_budget_item(event_id, item_data)
        return item
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create budget item: {str(e)}")

@event_router.put("/{event_id}/budget/items/{item_id}", response_model=BudgetItem)
async def update_budget_item(event_id: str, item_id: str, item_update: BudgetItemUpdate):
    """Update a specific budget item"""
    try:
        item = await mock_event_api.update_budget_item(event_id, item_id, item_update)
        if not item:
            raise HTTPException(status_code=404, detail="Budget item not found")
        return item
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update budget item: {str(e)}")

# Health check for events service
@event_router.get("/health/check")
async def events_health_check():
    """Health check for events service"""
    return {"status": "ok", "service": "events"}
