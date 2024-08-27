from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel
from google.oauth2 import id_token
from google.auth.transport import requests
from sqlalchemy.orm import Session
from app.db.database import get_db
import redis
from app.db.models import User  # Adjust this import based on your directory structure
from datetime import datetime, timezone, timedelta
import uuid
import logging
import time
import os
from jose import JWTError, jwt

# Initialize Redis connection
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)

router = APIRouter()

# Logger configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TokenData(BaseModel):
    access_token: str

class RefreshTokenData(BaseModel):
    refresh_token: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    user_info: dict

def verify_token(access_token: str):
    try:
        CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
        if not CLIENT_ID:
            raise ValueError("Google CLIENT_ID not found in environment variables.")
        
        # Verify the token using Google's library
        id_info = id_token.verify_oauth2_token(access_token, requests.Request(), CLIENT_ID, clock_skew_in_seconds=10)
        
        # Check if the token has expired
        if id_info.get("exp") < time.time():
            logger.error("Token has expired.")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
            )
        
        # Extract user info if token is valid and not expired
        user_info = {
            "name": id_info.get("name"),
            "given_name": id_info.get("given_name"),
            "picture": id_info.get("picture"),
            "email": id_info.get("email")
        }

        return user_info

    except ValueError as e:
        logger.error(f"Token verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token",
        )

def generate_refresh_token(user_info):
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
    ALGORITHM = "HS256"
    payload = {
        "sub": user_info['email'],
        "name": user_info.get('given_name', 'Unknown'),
        "exp": datetime.utcnow() + timedelta(days=30),  # Refresh token valid for 30 days
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def decode_refresh_token(refresh_token: str):
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
    ALGORITHM = "HS256"
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=403, detail="Invalid refresh token")

def get_current_user(authorization: str = Header(None), db: Session = Depends(get_db)):
    if authorization:
        token = authorization.split("Bearer ")[-1]
        try:
            # Verify the token and get user info
            user_info = verify_token(token)

            email = user_info['email']
            name = user_info.get('given_name', 'Unknown')

            # Check Redis cache
            cached_user = redis_client.get(f"user:{email}")
            if cached_user:
                logger.info(f"User found in cache: {email}")
                return user_info

            # Check if the user exists in the database
            user = db.query(User).filter(User.email == email).first()
            
            if not user:
                logger.info(f"User not found. Creating new user with email: {email}")
                user = User(
                    uuid=uuid.uuid4(),
                    email=email,
                    name=name,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc)
                )
                db.add(user)
                db.commit()
                db.refresh(user)
                logger.info(f"New user created with UUID: {user.uuid}, {user_info}")
            else:
                logger.info(f"User {user.email} found, verifying token")

            # Cache the user info
            redis_client.setex(f"user:{email}", 600, str(user_info))  # Cache for 10 minutes

            return user_info

        except HTTPException as e:
            logger.error(f"Authentication failed: {e.detail}")
            raise e
    raise HTTPException(status_code=401, detail="Authorization token is required")

@router.post("/token", response_model=TokenResponse)
def verify_jwt(token_data: TokenData, db: Session = Depends(get_db)):
    user_info = verify_token(token_data.access_token)
    refresh_token = generate_refresh_token(user_info)
    
    return TokenResponse(
        access_token=token_data.access_token,
        refresh_token=refresh_token,
        user_info=user_info
    )

@router.post("/refresh", response_model=TokenResponse)
def refresh_token(refresh_token_data: RefreshTokenData, db: Session = Depends(get_db)):
    try:
        # Decode the refresh token
        payload = decode_refresh_token(refresh_token_data.refresh_token)
        email = payload["sub"]
        user_info = {
            "email": email,
            "name": payload.get("name"),
            "given_name": payload.get("name"),
            "picture": payload.get("picture", '')
        }

        # Generate new access and refresh tokens
        new_access_token = generate_refresh_token(user_info)
        new_refresh_token = generate_refresh_token(user_info)

        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            user_info=user_info
        )
    
    except HTTPException as e:
        logger.error(f"Token refresh failed: {e.detail}")
        raise e
