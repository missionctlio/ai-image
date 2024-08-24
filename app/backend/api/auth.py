from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import User  # Adjust this import based on your directory structure
from app.db.schemas.user import UserCreate, UserRead  # Adjust this import based on your directory structure
from passlib.context import CryptContext
from datetime import datetime, timezone, timedelta
import uuid
import logging
from jose import JWTError, jwt
import os

router = APIRouter()

# Logger configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Password hashing utility
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Define the secret key and algorithm
SECRET_KEY = os.getenv("SECRET_KEY", "your_secret_key")  # Replace with a secure key in production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Utility functions for JWT handling
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise JWTError
        return user_id
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    access_token: str

@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    # Check if the user exists
    user = db.query(User).filter(User.email == request.email).first()

    if not user or not pwd_context.verify(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Generate JWT token for the user
    access_token = create_access_token(data={"sub": str(user.uuid)})
    
    return {"access_token": access_token}
