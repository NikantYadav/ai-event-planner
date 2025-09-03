import asyncio
import uuid
from typing import Dict, List
from datetime import datetime
from event_models import (
    EventFormData, EventPlanResponse, EventPlanSummary, 
    VendorRecommendation, TimelineItem, BudgetBreakdown
)

class MockEventAPI:
    def __init__(self):
        self.event_plans: Dict[str, EventPlanResponse] = {}
        
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

# Global instance
mock_event_api = MockEventAPI()
