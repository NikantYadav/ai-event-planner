from fastapi import APIRouter, HTTPException, Depends
from typing import List
from event_models import (
    EventFormData, EventPlanResponse, EventPlanSummary, EventPlanUpdate
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

# Health check for events service
@event_router.get("/health/check")
async def events_health_check():
    """Health check for events service"""
    return {"status": "ok", "service": "events"}
