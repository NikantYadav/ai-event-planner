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

# Task Management Models
class Task(BaseModel):
    id: str
    title: str
    description: str
    status: str  # 'pending', 'in_progress', 'completed'
    priority: str  # 'low', 'medium', 'high'
    category: str
    deadline: str
    assignedTo: Optional[str] = None
    createdAt: str
    updatedAt: str

class TaskCreate(BaseModel):
    title: str
    description: str
    priority: str
    category: str
    deadline: str
    assignedTo: Optional[str] = None

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    category: Optional[str] = None
    deadline: Optional[str] = None
    assignedTo: Optional[str] = None

# Vendor Management Models
class Vendor(BaseModel):
    id: str
    name: str
    category: str
    contactPerson: str
    email: str
    phone: str
    address: str
    website: Optional[str] = None
    rating: float
    priceRange: str
    description: str
    services: List[str]
    availability: str
    contractStatus: str  # 'not_contacted', 'contacted', 'quoted', 'booked', 'confirmed'
    quotedPrice: Optional[str] = None
    finalPrice: Optional[str] = None
    notes: Optional[str] = None
    createdAt: str
    updatedAt: str

class VendorCreate(BaseModel):
    name: str
    category: str
    contactPerson: str
    email: str
    phone: str
    address: str
    website: Optional[str] = None
    rating: float
    priceRange: str
    description: str
    services: List[str]
    availability: str

class VendorUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    contactPerson: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    website: Optional[str] = None
    rating: Optional[float] = None
    priceRange: Optional[str] = None
    description: Optional[str] = None
    services: Optional[List[str]] = None
    availability: Optional[str] = None
    contractStatus: Optional[str] = None
    quotedPrice: Optional[str] = None
    finalPrice: Optional[str] = None
    notes: Optional[str] = None

# Guest & RSVP Management Models
class Guest(BaseModel):
    id: str
    name: str
    email: str
    phone: Optional[str] = None
    rsvpStatus: str  # 'pending', 'attending', 'not_attending', 'maybe'
    dietaryRestrictions: Optional[str] = None
    plusOne: bool = False
    plusOneName: Optional[str] = None
    tableAssignment: Optional[str] = None
    specialRequests: Optional[str] = None
    invitationSent: bool = False
    invitationSentDate: Optional[str] = None
    rsvpDate: Optional[str] = None
    createdAt: str
    updatedAt: str

class GuestCreate(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    plusOne: bool = False
    dietaryRestrictions: Optional[str] = None
    specialRequests: Optional[str] = None

class GuestUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    rsvpStatus: Optional[str] = None
    dietaryRestrictions: Optional[str] = None
    plusOne: Optional[bool] = None
    plusOneName: Optional[str] = None
    tableAssignment: Optional[str] = None
    specialRequests: Optional[str] = None
    invitationSent: Optional[bool] = None
    invitationSentDate: Optional[str] = None
    rsvpDate: Optional[str] = None

# Budget Management Models
class BudgetItem(BaseModel):
    id: str
    category: str
    item: str
    estimatedCost: float
    actualCost: Optional[float] = None
    vendor: Optional[str] = None
    status: str  # 'planned', 'quoted', 'booked', 'paid'
    notes: Optional[str] = None
    createdAt: str
    updatedAt: str

class BudgetItemCreate(BaseModel):
    category: str
    item: str
    estimatedCost: float
    vendor: Optional[str] = None
    notes: Optional[str] = None

class BudgetItemUpdate(BaseModel):
    category: Optional[str] = None
    item: Optional[str] = None
    estimatedCost: Optional[float] = None
    actualCost: Optional[float] = None
    vendor: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None

class BudgetSummary(BaseModel):
    totalBudget: float
    totalSpent: float
    totalRemaining: float
    categoryBreakdown: List[BudgetBreakdown]
    items: List[BudgetItem]
