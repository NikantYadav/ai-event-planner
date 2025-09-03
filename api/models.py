from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime

class UserSignup(BaseModel):
    email: EmailStr
    password: str
    name: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    created_at: datetime

class Token(BaseModel):
    access_token: str
    token_type: str
    user: dict

class User(BaseModel):
    email: str
    password: str
    name: str
    events: List[str]

class Event(BaseModel):
    user: User  # Reference to a User object
    description: str
    vendor_cat: List[str] = []  # Array of vendor categories
    vendors: List[str] = []  