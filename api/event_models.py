from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# Event Planning Models
class EventFormData(BaseModel):
    eventType: str
    description: str
    location: str
    date: str
    budget: str
    guestCount: str
    duration: str

class VendorRecommendation(BaseModel):
    id: str
    name: str
    category: str
    rating: float
    price: str
    address: str
    phone: str
    website: str
    description: str

class TimelineItem(BaseModel):
    id: str
    time: str
    task: str
    status: str  # 'completed' | 'priority' | 'upcoming'
    description: str
    deadline: str

class BudgetBreakdown(BaseModel):
    category: str
    amount: int
    percentage: int
    description: str

class EventPlanResponse(BaseModel):
    id: str
    title: str
    eventType: str
    description: str
    location: str
    date: str
    budget: str
    guestCount: str
    duration: str
    vendors: List[VendorRecommendation]
    timeline: List[TimelineItem]
    budgetBreakdown: List[BudgetBreakdown]
    tips: List[str]
    checklist: List[str]
    createdAt: str
    updatedAt: str

class EventPlanSummary(BaseModel):
    id: str
    title: str
    type: str
    date: str
    budget: str
    guests: int
    status: str
    progress: int
    createdAt: str

class EventPlanUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    date: Optional[str] = None
    budget: Optional[str] = None
    guestCount: Optional[str] = None
    duration: Optional[str] = None
