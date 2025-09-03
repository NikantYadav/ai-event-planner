from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional
import jwt
import os
from pymongo.database import Database
from pymongo.errors import DuplicateKeyError
from bson import ObjectId
from models import UserSignup, UserLogin, UserResponse, Token
from mongo import get_db

# Initialize router
auth_router = APIRouter(prefix="/auth", tags=["Authentication"])

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM")
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES"))

# Security scheme
security = HTTPBearer()


def serialize_user(user: dict) -> dict:
    """Convert MongoDB user doc into JSON-serializable dict for frontend."""
    return {
        "id": str(user["_id"]),
        "email": user["email"],
        "name": user.get("name"),
        "events": user.get("events", []),
        "created_at": user["created_at"].isoformat() if isinstance(user["created_at"], datetime) else user["created_at"]
    }

def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token and return user data."""
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user_id
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_user(user_id: str = Depends(verify_token), db: Database = Depends(get_db)):
    """Get current user from database."""
    user = db.users.find_one({"_id": ObjectId(user_id)})
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    return user

@auth_router.post("/signup", response_model=Token, status_code=status.HTTP_201_CREATED)
async def signup(user_data: UserSignup, db: Database = Depends(get_db)):
    """Register a new user."""
    try:
        # Check if user already exists
        existing_user = db.users.find_one({"email": user_data.email})
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Hash password
        hashed_password = hash_password(user_data.password)
        
        # Create user document
        user_doc = {
            "email": user_data.email,
            "name": user_data.name,
            "password": hashed_password,
            "events": [],
            "created_at": datetime.utcnow()
        }
        
        # Insert user into database
        result = db.users.insert_one(user_doc)
        user_id = str(result.inserted_id)
        
        # Prepare safe user object (without password)
        user_doc["_id"] = user_id
        user_doc.pop("password", None)

        # Create access token
        access_token = create_access_token(data={"sub": user_id})
        
        return {"access_token": access_token, "token_type": "bearer", "user": serialize_user(user_doc)}
        
    except DuplicateKeyError:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )

@auth_router.post("/login", response_model=Token)
async def login(user_credentials: UserLogin, db: Database = Depends(get_db)):
    """Authenticate user and return JWT token."""
    # Find user by email
    user = db.users.find_one({"email": user_credentials.email})
    
    if not user or not verify_password(user_credentials.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token = create_access_token(data={"sub": str(user["_id"])})
    
    return {"access_token": access_token, "token_type": "bearer", "user": serialize_user(user)}

@auth_router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user = Depends(get_current_user)):
    """Get current user information."""
    return UserResponse(
        id=str(current_user["_id"]),
        email=current_user["email"],
        name=current_user["name"],
        created_at=current_user["created_at"]
    )