import asyncio
import uuid
from typing import Dict, List
from datetime import datetime
from event_models import (
    EventFormData, EventPlanResponse, EventPlanSummary, 
    VendorRecommendation, TimelineItem, BudgetBreakdown,
    Task, TaskCreate, TaskUpdate, Vendor, VendorCreate, VendorUpdate,
    Guest, GuestCreate, GuestUpdate, BudgetSummary, BudgetItem,
    BudgetItemCreate, BudgetItemUpdate
)

class MockEventAPI:
    def __init__(self):
        self.event_plans: Dict[str, EventPlanResponse] = {}
        self.event_tasks: Dict[str, List[Task]] = {}
        self.event_vendors: Dict[str, List[Vendor]] = {}
        self.event_guests: Dict[str, List[Guest]] = {}
        self.event_budgets: Dict[str, BudgetSummary] = {}
        
        # Mock vendor database
        self.mock_vendors = [
            VendorRecommendation(
                id='v1', name='Elegant Gardens Venue', category='venue', rating=4.8, price='$$$',
                address='123 Garden Lane, City Center', phone='(555) 123-4567',
                website='https://elegantgardens.com',
                description='Beautiful outdoor venue with manicured gardens and stunning views'
            ),
            VendorRecommendation(
                id='v2', name='Grand Ballroom Plaza', category='venue', rating=4.9, price='$$$$',
                address='456 Main Street, Downtown', phone='(555) 234-5678',
                website='https://grandballroom.com',
                description='Luxurious indoor venue perfect for elegant celebrations'
            ),
            VendorRecommendation(
                id='v3', name='Gourmet Catering Co.', category='catering', rating=4.7, price='$$$',
                address='789 Chef Avenue, Culinary District', phone='(555) 345-6789',
                website='https://gourmetcatering.com',
                description='Premium catering service with customizable menus'
            ),
            VendorRecommendation(
                id='v4', name='Fresh Bites Catering', category='catering', rating=4.6, price='$$',
                address='321 Food Street, Market Area', phone='(555) 456-7890',
                website='https://freshbites.com',
                description='Farm-to-table catering with fresh, local ingredients'
            ),
            VendorRecommendation(
                id='v5', name='Snapshot Studios', category='photography', rating=4.9, price='$$$',
                address='654 Artist Boulevard, Creative Quarter', phone='(555) 567-8901',
                website='https://snapshotstudios.com',
                description='Professional event photography with artistic flair'
            ),
            VendorRecommendation(
                id='v6', name='Memory Makers Photography', category='photography', rating=4.8, price='$$',
                address='987 Picture Lane, Photo District', phone='(555) 678-9012',
                website='https://memorymakers.com',
                description='Affordable professional photography for all events'
            ),
            VendorRecommendation(
                id='v7', name='Blooming Arrangements', category='flowers', rating=4.7, price='$$',
                address='159 Flower Street, Garden District', phone='(555) 789-0123',
                website='https://bloomingarrangements.com',
                description='Custom floral designs for every occasion'
            ),
            VendorRecommendation(
                id='v8', name='Harmony Musicians', category='entertainment', rating=4.8, price='$$$',
                address='753 Music Avenue, Arts District', phone='(555) 890-1234',
                website='https://harmonymusicians.com',
                description='Professional musicians and entertainment for events'
            )
        ]
        
        # Timeline templates
        self.timeline_templates = {
            'wedding': [
                {'time': '6 months', 'task': 'Book venue and send save-the-dates', 'status': 'priority', 
                 'description': 'Secure your preferred venue and notify guests', 'deadline': '6 months before'},
                {'time': '4 months', 'task': 'Finalize catering and photography', 'status': 'upcoming',
                 'description': 'Lock in your menu and photographer', 'deadline': '4 months before'},
                {'time': '3 months', 'task': 'Send formal invitations', 'status': 'upcoming',
                 'description': 'Mail wedding invitations with RSVP details', 'deadline': '3 months before'},
                {'time': '2 months', 'task': 'Confirm all vendors', 'status': 'upcoming',
                 'description': 'Final confirmation calls with all vendors', 'deadline': '2 months before'},
                {'time': '1 month', 'task': 'Final headcount and details', 'status': 'upcoming',
                 'description': 'Provide final guest count and special requirements', 'deadline': '1 month before'},
                {'time': '1 week', 'task': 'Final rehearsal and setup', 'status': 'upcoming',
                 'description': 'Rehearsal dinner and venue setup confirmation', 'deadline': '1 week before'}
            ],
            'birthday': [
                {'time': '1 month', 'task': 'Plan theme and guest list', 'status': 'priority',
                 'description': 'Decide on party theme and create guest list', 'deadline': '1 month before'},
                {'time': '3 weeks', 'task': 'Send invitations', 'status': 'upcoming',
                 'description': 'Send digital or physical invitations', 'deadline': '3 weeks before'},
                {'time': '2 weeks', 'task': 'Order decorations and cake', 'status': 'upcoming',
                 'description': 'Purchase decorations and order custom cake', 'deadline': '2 weeks before'},
                {'time': '1 week', 'task': 'Confirm RSVPs and finalize details', 'status': 'upcoming',
                 'description': 'Follow up on RSVPs and confirm all arrangements', 'deadline': '1 week before'},
                {'time': '2 days', 'task': 'Prepare venue and decorations', 'status': 'upcoming',
                 'description': 'Set up decorations and prepare party space', 'deadline': '2 days before'}
            ],
            'corporate': [
                {'time': '3 months', 'task': 'Secure venue and set agenda', 'status': 'priority',
                 'description': 'Book corporate venue and outline event agenda', 'deadline': '3 months before'},
                {'time': '2 months', 'task': 'Arrange catering and AV equipment', 'status': 'upcoming',
                 'description': 'Book catering service and audio/visual setup', 'deadline': '2 months before'},
                {'time': '6 weeks', 'task': 'Send invitations to attendees', 'status': 'upcoming',
                 'description': 'Distribute formal invitations with agenda', 'deadline': '6 weeks before'},
                {'time': '1 month', 'task': 'Confirm speakers and presentations', 'status': 'upcoming',
                 'description': 'Final confirmation with all speakers', 'deadline': '1 month before'},
                {'time': '1 week', 'task': 'Final headcount and logistics', 'status': 'upcoming',
                 'description': 'Confirm attendance and final arrangements', 'deadline': '1 week before'}
            ]
        }
        
        # Budget templates
        self.budget_templates = {
            'wedding': [
                {'category': 'Venue', 'percentage': 40, 'description': 'Reception and ceremony location'},
                {'category': 'Catering', 'percentage': 30, 'description': 'Food and beverages'},
                {'category': 'Photography', 'percentage': 10, 'description': 'Professional photography and videography'},
                {'category': 'Flowers & Decorations', 'percentage': 8, 'description': 'Floral arrangements and decor'},
                {'category': 'Entertainment', 'percentage': 7, 'description': 'Music and entertainment'},
                {'category': 'Miscellaneous', 'percentage': 5, 'description': 'Transportation, favors, and other expenses'}
            ],
            'birthday': [
                {'category': 'Venue', 'percentage': 35, 'description': 'Party location rental'},
                {'category': 'Catering', 'percentage': 30, 'description': 'Food, drinks, and cake'},
                {'category': 'Decorations', 'percentage': 20, 'description': 'Themed decorations and supplies'},
                {'category': 'Entertainment', 'percentage': 10, 'description': 'Activities and entertainment'},
                {'category': 'Miscellaneous', 'percentage': 5, 'description': 'Party favors and extras'}
            ],
            'corporate': [
                {'category': 'Venue', 'percentage': 35, 'description': 'Meeting space and facilities'},
                {'category': 'Catering', 'percentage': 25, 'description': 'Meals and refreshments'},
                {'category': 'AV Equipment', 'percentage': 15, 'description': 'Audio/visual technology'},
                {'category': 'Speakers/Presenters', 'percentage': 15, 'description': 'Speaker fees and travel'},
                {'category': 'Materials', 'percentage': 5, 'description': 'Printed materials and supplies'},
                {'category': 'Miscellaneous', 'percentage': 5, 'description': 'Transportation and extras'}
            ]
        }

    async def generate_event_plan(self, form_data: EventFormData) -> EventPlanResponse:
        """Generate a mock event plan based on form data"""
        # Simulate API processing time
        await asyncio.sleep(2 + (0.5 * 2))  # 2-3 seconds
        
        event_id = f"event_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:9]}"
        event_type_key = form_data.eventType.lower().replace(' ', '')
        
        # Select relevant vendors based on event type
        relevant_vendors = self._get_relevant_vendors(form_data.eventType)
        
        # Generate timeline
        timeline_template = self.timeline_templates.get(event_type_key, self.timeline_templates['birthday'])
        timeline = [
            TimelineItem(
                id=f"timeline_{i}",
                time=item['time'],
                task=item['task'],
                status=item['status'],
                description=item['description'],
                deadline=item['deadline']
            ) for i, item in enumerate(timeline_template)
        ]
        
        # Generate budget breakdown
        budget_template = self.budget_templates.get(event_type_key, self.budget_templates['birthday'])
        total_budget = int(''.join(filter(str.isdigit, form_data.budget))) if form_data.budget else 10000
        budget_breakdown = [
            BudgetBreakdown(
                category=item['category'],
                amount=round((total_budget * item['percentage']) / 100),
                percentage=item['percentage'],
                description=item['description']
            ) for item in budget_template
        ]
        
        # Generate tips and checklist
        tips = self._generate_tips(form_data.eventType)
        checklist = self._generate_checklist(form_data.eventType)
        
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
            vendors=relevant_vendors,
            timeline=timeline,
            budgetBreakdown=budget_breakdown,
            tips=tips,
            checklist=checklist,
            createdAt=datetime.now().isoformat(),
            updatedAt=datetime.now().isoformat()
        )
        
        # Store the plan
        self.event_plans[event_id] = event_plan
        
        # Generate sample tasks for the event
        self._generate_sample_tasks(event_id, form_data.eventType)
        
        # Generate sample vendors for the event
        self._generate_sample_vendors(event_id, form_data.eventType)
        
        # Generate sample guests for the event
        self._generate_sample_guests(event_id)
        
        return event_plan

    async def get_event_plans(self) -> List[EventPlanSummary]:
        """Get all event plans"""
        await asyncio.sleep(0.5)
        
        return [
            EventPlanSummary(
                id=plan.id,
                title=plan.title,
                type=plan.eventType,
                date=plan.date,
                budget=plan.budget,
                guests=int(plan.guestCount) if plan.guestCount.isdigit() else 0,
                status=self._calculate_status(plan),
                progress=self._calculate_progress(plan),
                createdAt=plan.createdAt
            ) for plan in self.event_plans.values()
        ]

    async def get_event_plan(self, event_id: str) -> EventPlanResponse:
        """Get a specific event plan"""
        await asyncio.sleep(0.3)
        return self.event_plans.get(event_id)

    async def update_event_plan(self, event_id: str, updates: dict) -> EventPlanResponse:
        """Update an event plan"""
        await asyncio.sleep(0.8)
        
        existing_plan = self.event_plans.get(event_id)
        if not existing_plan:
            return None
            
        # Update the plan
        plan_dict = existing_plan.dict()
        plan_dict.update(updates)
        plan_dict['updatedAt'] = datetime.now().isoformat()
        
        updated_plan = EventPlanResponse(**plan_dict)
        self.event_plans[event_id] = updated_plan
        return updated_plan

    async def delete_event_plan(self, event_id: str) -> bool:
        """Delete an event plan"""
        await asyncio.sleep(0.3)
        return self.event_plans.pop(event_id, None) is not None

    def _get_relevant_vendors(self, event_type: str) -> List[VendorRecommendation]:
        """Get relevant vendors based on event type"""
        event_type_lower = event_type.lower()
        categories = []
        
        if 'wedding' in event_type_lower:
            categories = ['venue', 'catering', 'photography', 'flowers', 'entertainment']
        elif 'birthday' in event_type_lower:
            categories = ['venue', 'catering', 'entertainment']
        elif 'corporate' in event_type_lower:
            categories = ['venue', 'catering']
        else:
            categories = ['venue', 'catering', 'entertainment']
        
        relevant_vendors = []
        for category in categories:
            category_vendors = [v for v in self.mock_vendors if v.category == category][:2]
            relevant_vendors.extend(category_vendors)
        
        return relevant_vendors

    def _generate_event_title(self, form_data: EventFormData) -> str:
        """Generate an event title"""
        event_type = form_data.eventType
        try:
            date = datetime.fromisoformat(form_data.date.replace('Z', '+00:00'))
            month_year = date.strftime('%B %Y')
        except:
            month_year = 'TBD'
        
        if 'wedding' in event_type.lower():
            return f"Wedding Celebration - {month_year}"
        elif 'birthday' in event_type.lower():
            return f"Birthday Party - {month_year}"
        elif 'corporate' in event_type.lower():
            return f"Corporate Event - {month_year}"
        else:
            return f"{event_type} - {month_year}"

    def _generate_tips(self, event_type: str) -> List[str]:
        """Generate tips based on event type"""
        event_type_lower = event_type.lower()
        
        if 'wedding' in event_type_lower:
            return [
                'Book your venue at least 6 months in advance for popular dates',
                'Consider a weekday or off-season wedding to save on costs',
                'Create a detailed timeline and share it with all vendors',
                'Have a backup plan for outdoor ceremonies',
                "Don't forget to eat during your reception!"
            ]
        elif 'birthday' in event_type_lower:
            return [
                'Send invitations at least 2-3 weeks in advance',
                'Consider dietary restrictions when planning the menu',
                'Have backup indoor activities if planning an outdoor party',
                'Delegate tasks to friends and family to reduce stress',
                'Take lots of photos to capture the memories'
            ]
        elif 'corporate' in event_type_lower:
            return [
                'Test all AV equipment before the event starts',
                'Provide clear signage and directions for attendees',
                'Have a registration desk with name badges ready',
                'Plan networking breaks between presentations',
                'Follow up with attendees after the event'
            ]
        else:
            return [
                'Plan ahead and book vendors early',
                'Stay within your budget by prioritizing must-haves',
                'Create a detailed timeline for the day',
                'Have a backup plan for any outdoor elements',
                'Delegate responsibilities to reduce stress'
            ]

    def _generate_checklist(self, event_type: str) -> List[str]:
        """Generate checklist based on event type"""
        event_type_lower = event_type.lower()
        
        if 'wedding' in event_type_lower:
            return [
                'Venue booked and contract signed',
                'Catering menu finalized',
                'Photographer/videographer confirmed',
                'Wedding dress and attire ready',
                'Invitations sent and RSVPs tracked',
                'Marriage license obtained',
                'Rehearsal dinner planned',
                'Emergency kit prepared'
            ]
        elif 'birthday' in event_type_lower:
            return [
                'Guest list finalized',
                'Invitations sent',
                'Venue decorated',
                'Food and cake ordered',
                'Entertainment arranged',
                'Camera/photographer ready',
                'Party favors prepared',
                'Music playlist created'
            ]
        elif 'corporate' in event_type_lower:
            return [
                'Venue set up with proper seating',
                'AV equipment tested',
                'Catering confirmed and ready',
                'Speakers briefed and materials ready',
                'Registration area prepared',
                'Name badges and materials printed',
                'Welcome signage displayed',
                'Emergency contacts available'
            ]
        else:
            return [
                'Venue prepared and decorated',
                'Catering arrangements confirmed',
                'All vendors contacted',
                'Guest list and RSVPs managed',
                'Timeline shared with key people',
                'Emergency plan in place',
                'Photography arranged',
                'Cleanup plan ready'
            ]

    def _calculate_status(self, plan: EventPlanResponse) -> str:
        """Calculate event status"""
        try:
            event_date = datetime.fromisoformat(plan.date.replace('Z', '+00:00'))
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
        except:
            return 'Planning'

    def _calculate_progress(self, plan: EventPlanResponse) -> int:
        """Calculate event progress"""
        try:
            event_date = datetime.fromisoformat(plan.date.replace('Z', '+00:00'))
            created_date = datetime.fromisoformat(plan.createdAt.replace('Z', '+00:00'))
            now = datetime.now()
            
            total_time = (event_date - created_date).total_seconds()
            elapsed_time = (now - created_date).total_seconds()
            
            if total_time <= 0:
                return 100
                
            progress = max(0, min(100, (elapsed_time / total_time) * 100))
            return round(progress)
        except:
            return 0

    # Task Management Methods
    async def get_event_tasks(self, event_id: str) -> List[Task]:
        """Get all tasks for an event"""
        await asyncio.sleep(0.3)
        return self.event_tasks.get(event_id, [])

    async def create_event_task(self, event_id: str, task_data: TaskCreate) -> Task:
        """Create a new task for an event"""
        await asyncio.sleep(0.5)
        
        task_id = f"task_{uuid.uuid4().hex[:8]}"
        task = Task(
            id=task_id,
            title=task_data.title,
            description=task_data.description,
            status="pending",
            priority=task_data.priority,
            category=task_data.category,
            deadline=task_data.deadline,
            assignedTo=task_data.assignedTo,
            createdAt=datetime.now().isoformat(),
            updatedAt=datetime.now().isoformat()
        )
        
        if event_id not in self.event_tasks:
            self.event_tasks[event_id] = []
        self.event_tasks[event_id].append(task)
        
        return task

    async def update_event_task(self, event_id: str, task_id: str, task_update: TaskUpdate) -> Task:
        """Update a task"""
        await asyncio.sleep(0.3)
        
        tasks = self.event_tasks.get(event_id, [])
        for i, task in enumerate(tasks):
            if task.id == task_id:
                task_dict = task.dict()
                update_dict = {k: v for k, v in task_update.dict().items() if v is not None}
                task_dict.update(update_dict)
                task_dict['updatedAt'] = datetime.now().isoformat()
                
                updated_task = Task(**task_dict)
                self.event_tasks[event_id][i] = updated_task
                return updated_task
        
        return None

    # Vendor Management Methods
    async def get_event_vendors(self, event_id: str) -> List[Vendor]:
        """Get all vendors for an event"""
        await asyncio.sleep(0.3)
        return self.event_vendors.get(event_id, [])

    async def create_event_vendor(self, event_id: str, vendor_data: VendorCreate) -> Vendor:
        """Create a new vendor for an event"""
        await asyncio.sleep(0.5)
        
        vendor_id = f"vendor_{uuid.uuid4().hex[:8]}"
        vendor = Vendor(
            id=vendor_id,
            name=vendor_data.name,
            category=vendor_data.category,
            contactPerson=vendor_data.contactPerson,
            email=vendor_data.email,
            phone=vendor_data.phone,
            address=vendor_data.address,
            website=vendor_data.website,
            rating=vendor_data.rating,
            priceRange=vendor_data.priceRange,
            description=vendor_data.description,
            services=vendor_data.services,
            availability=vendor_data.availability,
            contractStatus="not_contacted",
            createdAt=datetime.now().isoformat(),
            updatedAt=datetime.now().isoformat()
        )
        
        if event_id not in self.event_vendors:
            self.event_vendors[event_id] = []
        self.event_vendors[event_id].append(vendor)
        
        return vendor

    async def update_event_vendor(self, event_id: str, vendor_id: str, vendor_update: VendorUpdate) -> Vendor:
        """Update a vendor"""
        await asyncio.sleep(0.3)
        
        vendors = self.event_vendors.get(event_id, [])
        for i, vendor in enumerate(vendors):
            if vendor.id == vendor_id:
                vendor_dict = vendor.dict()
                update_dict = {k: v for k, v in vendor_update.dict().items() if v is not None}
                vendor_dict.update(update_dict)
                vendor_dict['updatedAt'] = datetime.now().isoformat()
                
                updated_vendor = Vendor(**vendor_dict)
                self.event_vendors[event_id][i] = updated_vendor
                return updated_vendor
        
        return None

    # Guest Management Methods
    async def get_event_guests(self, event_id: str) -> List[Guest]:
        """Get all guests for an event"""
        await asyncio.sleep(0.3)
        return self.event_guests.get(event_id, [])

    async def create_event_guest(self, event_id: str, guest_data: GuestCreate) -> Guest:
        """Create a new guest for an event"""
        await asyncio.sleep(0.5)
        
        guest_id = f"guest_{uuid.uuid4().hex[:8]}"
        guest = Guest(
            id=guest_id,
            name=guest_data.name,
            email=guest_data.email,
            phone=guest_data.phone,
            rsvpStatus="pending",
            dietaryRestrictions=guest_data.dietaryRestrictions,
            plusOne=guest_data.plusOne,
            specialRequests=guest_data.specialRequests,
            invitationSent=False,
            createdAt=datetime.now().isoformat(),
            updatedAt=datetime.now().isoformat()
        )
        
        if event_id not in self.event_guests:
            self.event_guests[event_id] = []
        self.event_guests[event_id].append(guest)
        
        return guest

    async def update_event_guest(self, event_id: str, guest_id: str, guest_update: GuestUpdate) -> Guest:
        """Update a guest"""
        await asyncio.sleep(0.3)
        
        guests = self.event_guests.get(event_id, [])
        for i, guest in enumerate(guests):
            if guest.id == guest_id:
                guest_dict = guest.dict()
                update_dict = {k: v for k, v in guest_update.dict().items() if v is not None}
                guest_dict.update(update_dict)
                guest_dict['updatedAt'] = datetime.now().isoformat()
                
                updated_guest = Guest(**guest_dict)
                self.event_guests[event_id][i] = updated_guest
                return updated_guest
        
        return None

    # Budget Management Methods
    async def get_event_budget(self, event_id: str) -> BudgetSummary:
        """Get budget summary for an event"""
        await asyncio.sleep(0.3)
        
        if event_id in self.event_budgets:
            return self.event_budgets[event_id]
        
        # Generate default budget if none exists
        event_plan = self.event_plans.get(event_id)
        if not event_plan:
            return None
            
        total_budget = float(''.join(filter(str.isdigit, event_plan.budget))) if event_plan.budget else 10000.0
        
        # Create sample budget items
        budget_items = [
            BudgetItem(
                id=f"budget_{i}",
                category=breakdown.category,
                item=f"{breakdown.category} Services",
                estimatedCost=float(breakdown.amount),
                status="planned",
                createdAt=datetime.now().isoformat(),
                updatedAt=datetime.now().isoformat()
            ) for i, breakdown in enumerate(event_plan.budgetBreakdown)
        ]
        
        total_spent = sum(item.actualCost or 0 for item in budget_items)
        
        budget_summary = BudgetSummary(
            totalBudget=total_budget,
            totalSpent=total_spent,
            totalRemaining=total_budget - total_spent,
            categoryBreakdown=event_plan.budgetBreakdown,
            items=budget_items
        )
        
        self.event_budgets[event_id] = budget_summary
        return budget_summary

    async def create_budget_item(self, event_id: str, item_data: BudgetItemCreate) -> BudgetItem:
        """Create a new budget item"""
        await asyncio.sleep(0.5)
        
        item_id = f"budget_{uuid.uuid4().hex[:8]}"
        budget_item = BudgetItem(
            id=item_id,
            category=item_data.category,
            item=item_data.item,
            estimatedCost=item_data.estimatedCost,
            vendor=item_data.vendor,
            status="planned",
            notes=item_data.notes,
            createdAt=datetime.now().isoformat(),
            updatedAt=datetime.now().isoformat()
        )
        
        # Get or create budget summary
        budget_summary = await self.get_event_budget(event_id)
        if budget_summary:
            budget_summary.items.append(budget_item)
            self.event_budgets[event_id] = budget_summary
        
        return budget_item

    async def update_budget_item(self, event_id: str, item_id: str, item_update: BudgetItemUpdate) -> BudgetItem:
        """Update a budget item"""
        await asyncio.sleep(0.3)
        
        budget_summary = self.event_budgets.get(event_id)
        if not budget_summary:
            return None
            
        for i, item in enumerate(budget_summary.items):
            if item.id == item_id:
                item_dict = item.dict()
                update_dict = {k: v for k, v in item_update.dict().items() if v is not None}
                item_dict.update(update_dict)
                item_dict['updatedAt'] = datetime.now().isoformat()
                
                updated_item = BudgetItem(**item_dict)
                budget_summary.items[i] = updated_item
                
                # Recalculate totals
                budget_summary.totalSpent = sum(item.actualCost or 0 for item in budget_summary.items)
                budget_summary.totalRemaining = budget_summary.totalBudget - budget_summary.totalSpent
                
                self.event_budgets[event_id] = budget_summary
                return updated_item
        
        return None

    def _generate_sample_tasks(self, event_id: str, event_type: str):
        """Generate sample tasks based on event type"""
        event_type_lower = event_type.lower()
        
        if 'wedding' in event_type_lower:
            sample_tasks = [
                {"title": "Book venue and send save-the-dates", "description": "Secure your dream venue and notify guests early", "priority": "high", "category": "Venue", "deadline": "6 months before"},
                {"title": "Finalize catering menu", "description": "Confirm menu options and dietary requirements", "priority": "high", "category": "Catering", "deadline": "4 months before"},
                {"title": "Book photographer", "description": "Secure photography services for the big day", "priority": "medium", "category": "Photography", "deadline": "4 months before"},
                {"title": "Send formal invitations", "description": "Mail wedding invitations with RSVP details", "priority": "medium", "category": "Invitations", "deadline": "3 months before"},
                {"title": "Final vendor confirmations", "description": "Confirm all arrangements with vendors", "priority": "high", "category": "Coordination", "deadline": "1 month before"}
            ]
        elif 'birthday' in event_type_lower:
            sample_tasks = [
                {"title": "Plan theme and guest list", "description": "Decide on party theme and create guest list", "priority": "high", "category": "Planning", "deadline": "1 month before"},
                {"title": "Send invitations", "description": "Send digital or physical invitations", "priority": "medium", "category": "Invitations", "deadline": "3 weeks before"},
                {"title": "Order decorations and cake", "description": "Purchase decorations and order custom cake", "priority": "medium", "category": "Decorations", "deadline": "2 weeks before"},
                {"title": "Confirm RSVPs", "description": "Follow up on RSVPs and finalize headcount", "priority": "high", "category": "Coordination", "deadline": "1 week before"}
            ]
        else:
            sample_tasks = [
                {"title": "Secure venue", "description": "Book event venue and confirm availability", "priority": "high", "category": "Venue", "deadline": "2 months before"},
                {"title": "Arrange catering", "description": "Book catering service for the event", "priority": "medium", "category": "Catering", "deadline": "1 month before"},
                {"title": "Send invitations", "description": "Distribute event invitations to attendees", "priority": "medium", "category": "Invitations", "deadline": "3 weeks before"},
                {"title": "Final preparations", "description": "Complete final setup and arrangements", "priority": "high", "category": "Setup", "deadline": "1 week before"}
            ]
        
        tasks = []
        for i, task_data in enumerate(sample_tasks):
            task = Task(
                id=f"task_{uuid.uuid4().hex[:8]}",
                title=task_data["title"],
                description=task_data["description"],
                status="pending",
                priority=task_data["priority"],
                category=task_data["category"],
                deadline=task_data["deadline"],
                createdAt=datetime.now().isoformat(),
                updatedAt=datetime.now().isoformat()
            )
            tasks.append(task)
        
        self.event_tasks[event_id] = tasks

    def _generate_sample_vendors(self, event_id: str, event_type: str):
        """Generate sample vendors based on event type"""
        event_type_lower = event_type.lower()
        
        sample_vendors = []
        
        if 'wedding' in event_type_lower:
            sample_vendors = [
                {
                    "name": "Elegant Gardens Venue",
                    "category": "Venue",
                    "contactPerson": "Sarah Johnson",
                    "email": "sarah@elegantgardens.com",
                    "phone": "(555) 123-4567",
                    "address": "123 Garden Lane, City Center",
                    "website": "https://elegantgardens.com",
                    "rating": 4.8,
                    "priceRange": "$$$$",
                    "description": "Beautiful outdoor venue with manicured gardens",
                    "services": ["Ceremony Space", "Reception Hall", "Bridal Suite", "Catering Kitchen"],
                    "availability": "Available"
                },
                {
                    "name": "Gourmet Catering Co.",
                    "category": "Catering",
                    "contactPerson": "Chef Michael Brown",
                    "email": "michael@gourmetcatering.com",
                    "phone": "(555) 234-5678",
                    "address": "789 Chef Avenue, Culinary District",
                    "rating": 4.7,
                    "priceRange": "$$$",
                    "description": "Premium catering with customizable menus",
                    "services": ["Wedding Cakes", "Cocktail Hour", "Plated Dinner", "Buffet Service"],
                    "availability": "Available"
                }
            ]
        elif 'birthday' in event_type_lower:
            sample_vendors = [
                {
                    "name": "Party Palace",
                    "category": "Venue",
                    "contactPerson": "Lisa Martinez",
                    "email": "lisa@partypalace.com",
                    "phone": "(555) 345-6789",
                    "address": "456 Party Street, Entertainment District",
                    "rating": 4.5,
                    "priceRange": "$$",
                    "description": "Fun venue perfect for birthday celebrations",
                    "services": ["Party Rooms", "Sound System", "Decorations", "Games"],
                    "availability": "Available"
                }
            ]
        else:
            sample_vendors = [
                {
                    "name": "Corporate Center",
                    "category": "Venue",
                    "contactPerson": "David Wilson",
                    "email": "david@corporatecenter.com",
                    "phone": "(555) 456-7890",
                    "address": "789 Business Blvd, Corporate District",
                    "rating": 4.6,
                    "priceRange": "$$$",
                    "description": "Professional venue for corporate events",
                    "services": ["Conference Rooms", "AV Equipment", "Catering Kitchen", "Parking"],
                    "availability": "Available"
                }
            ]
        
        vendors = []
        for vendor_data in sample_vendors:
            vendor = Vendor(
                id=f"vendor_{uuid.uuid4().hex[:8]}",
                name=vendor_data["name"],
                category=vendor_data["category"],
                contactPerson=vendor_data["contactPerson"],
                email=vendor_data["email"],
                phone=vendor_data["phone"],
                address=vendor_data["address"],
                website=vendor_data.get("website"),
                rating=vendor_data["rating"],
                priceRange=vendor_data["priceRange"],
                description=vendor_data["description"],
                services=vendor_data["services"],
                availability=vendor_data["availability"],
                contractStatus="not_contacted",
                createdAt=datetime.now().isoformat(),
                updatedAt=datetime.now().isoformat()
            )
            vendors.append(vendor)
        
        self.event_vendors[event_id] = vendors

    def _generate_sample_guests(self, event_id: str):
        """Generate sample guests for the event"""
        sample_guests_data = [
            {"name": "John Smith", "email": "john.smith@email.com", "phone": "(555) 111-2222", "rsvpStatus": "attending"},
            {"name": "Emily Johnson", "email": "emily.johnson@email.com", "phone": "(555) 333-4444", "rsvpStatus": "pending", "plusOne": True},
            {"name": "Michael Brown", "email": "michael.brown@email.com", "rsvpStatus": "maybe", "dietaryRestrictions": "Vegetarian"},
            {"name": "Sarah Davis", "email": "sarah.davis@email.com", "phone": "(555) 555-6666", "rsvpStatus": "attending", "plusOne": True, "plusOneName": "Tom Davis"},
            {"name": "Robert Wilson", "email": "robert.wilson@email.com", "rsvpStatus": "not_attending"}
        ]
        
        guests = []
        for guest_data in sample_guests_data:
            guest = Guest(
                id=f"guest_{uuid.uuid4().hex[:8]}",
                name=guest_data["name"],
                email=guest_data["email"],
                phone=guest_data.get("phone"),
                rsvpStatus=guest_data["rsvpStatus"],
                dietaryRestrictions=guest_data.get("dietaryRestrictions"),
                plusOne=guest_data.get("plusOne", False),
                plusOneName=guest_data.get("plusOneName"),
                invitationSent=True,
                invitationSentDate=datetime.now().isoformat(),
                rsvpDate=datetime.now().isoformat() if guest_data["rsvpStatus"] != "pending" else None,
                createdAt=datetime.now().isoformat(),
                updatedAt=datetime.now().isoformat()
            )
            guests.append(guest)
        
        self.event_guests[event_id] = guests

# Global instance
mock_event_api = MockEventAPI()
