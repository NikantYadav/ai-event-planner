from fastapi import APIRouter, HTTPException, Depends
from typing import List
from event_models import (
    EventFormData, EventPlanResponse, EventPlanSummary, EventPlanUpdate,
    Task, TaskCreate, TaskUpdate, Vendor, VendorCreate, VendorUpdate,
    Guest, GuestCreate, GuestUpdate, BudgetSummary, BudgetItem, 
    BudgetItemCreate, BudgetItemUpdate
)
from mock_event_service import mock_event_api

# Create router for event planning endpoints
event_router = APIRouter(prefix="/api/events", tags=["events"])

@event_router.post("/generate", response_model=EventPlanResponse)
async def generate_event_plan(form_data: EventFormData):
    """Generate a new event plan based on form data"""
    try:
        event_plan = await mock_event_api.generate_event_plan(form_data)
        return event_plan
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate event plan: {str(e)}")

@event_router.get("/", response_model=List[EventPlanSummary])
async def get_event_plans():
    """Get all event plans for the current user"""
    try:
        plans = await mock_event_api.get_event_plans()
        return plans
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch event plans: {str(e)}")

@event_router.get("/{event_id}", response_model=EventPlanResponse)
async def get_event_plan(event_id: str):
    """Get a specific event plan by ID"""
    try:
        plan = await mock_event_api.get_event_plan(event_id)
        if not plan:
            raise HTTPException(status_code=404, detail="Event plan not found")
        return plan
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch event plan: {str(e)}")

@event_router.put("/{event_id}", response_model=EventPlanResponse)
async def update_event_plan(event_id: str, updates: EventPlanUpdate):
    """Update an existing event plan"""
    try:
        # Convert to dict and remove None values
        update_data = {k: v for k, v in updates.dict().items() if v is not None}
        
        updated_plan = await mock_event_api.update_event_plan(event_id, update_data)
        if not updated_plan:
            raise HTTPException(status_code=404, detail="Event plan not found")
        return updated_plan
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update event plan: {str(e)}")

@event_router.delete("/{event_id}")
async def delete_event_plan(event_id: str):
    """Delete an event plan"""
    try:
        success = await mock_event_api.delete_event_plan(event_id)
        if not success:
            raise HTTPException(status_code=404, detail="Event plan not found")
        return {"message": "Event plan deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete event plan: {str(e)}")

# Task Management Endpoints
@event_router.get("/{event_id}/tasks", response_model=List[Task])
async def get_event_tasks(event_id: str):
    """Get all tasks for a specific event"""
    try:
        tasks = await mock_event_api.get_event_tasks(event_id)
        return tasks
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch tasks: {str(e)}")

@event_router.post("/{event_id}/tasks", response_model=Task)
async def create_event_task(event_id: str, task_data: TaskCreate):
    """Create a new task for an event"""
    try:
        task = await mock_event_api.create_event_task(event_id, task_data)
        return task
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create task: {str(e)}")

@event_router.put("/{event_id}/tasks/{task_id}", response_model=Task)
async def update_event_task(event_id: str, task_id: str, task_update: TaskUpdate):
    """Update a specific task"""
    try:
        task = await mock_event_api.update_event_task(event_id, task_id, task_update)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        return task
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update task: {str(e)}")

# Vendor Management Endpoints
@event_router.get("/{event_id}/vendors", response_model=List[Vendor])
async def get_event_vendors(event_id: str):
    """Get all vendors for a specific event"""
    try:
        vendors = await mock_event_api.get_event_vendors(event_id)
        return vendors
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch vendors: {str(e)}")

@event_router.post("/{event_id}/vendors", response_model=Vendor)
async def create_event_vendor(event_id: str, vendor_data: VendorCreate):
    """Add a new vendor to an event"""
    try:
        vendor = await mock_event_api.create_event_vendor(event_id, vendor_data)
        return vendor
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create vendor: {str(e)}")

@event_router.put("/{event_id}/vendors/{vendor_id}", response_model=Vendor)
async def update_event_vendor(event_id: str, vendor_id: str, vendor_update: VendorUpdate):
    """Update a specific vendor"""
    try:
        vendor = await mock_event_api.update_event_vendor(event_id, vendor_id, vendor_update)
        if not vendor:
            raise HTTPException(status_code=404, detail="Vendor not found")
        return vendor
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update vendor: {str(e)}")

# Guest & RSVP Management Endpoints
@event_router.get("/{event_id}/guests", response_model=List[Guest])
async def get_event_guests(event_id: str):
    """Get all guests for a specific event"""
    try:
        guests = await mock_event_api.get_event_guests(event_id)
        return guests
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch guests: {str(e)}")

@event_router.post("/{event_id}/guests", response_model=Guest)
async def create_event_guest(event_id: str, guest_data: GuestCreate):
    """Add a new guest to an event"""
    try:
        guest = await mock_event_api.create_event_guest(event_id, guest_data)
        return guest
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create guest: {str(e)}")

@event_router.put("/{event_id}/guests/{guest_id}", response_model=Guest)
async def update_event_guest(event_id: str, guest_id: str, guest_update: GuestUpdate):
    """Update a specific guest"""
    try:
        guest = await mock_event_api.update_event_guest(event_id, guest_id, guest_update)
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
