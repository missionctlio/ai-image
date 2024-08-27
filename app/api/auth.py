from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel
from google.oauth2 import id_token
from google.auth.transport import requests
from sqlalchemy.orm import Session
from app.db.database import get_db
import redis
from app.db.models import User  # Adjust this import based on your directory structure
from datetime import datetime, timezone
import uuid
import logging
import os

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

def get_current_user(authorization: str = Header(None), db: Session = Depends(get_db)):
    if authorization:
        token = authorization.split("Bearer ")[-1]
        try:
            # Verify the token
            CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
            if not CLIENT_ID:
                raise ValueError("Google CLIENT_ID not found in environment variables.")

            id_info = id_token.verify_oauth2_token(token, requests.Request(), CLIENT_ID, clock_skew_in_seconds=10)
            user_info = {
                "name": id_info.get("name"),
                "given_name": id_info.get("given_name"),
                "picture": id_info.get("picture"),
                "email": id_info.get("email")
            }

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

        except ValueError as e:
            logger.error(f"Token verification failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e),
            )
    raise HTTPException(status_code=401, detail="Authorization token is required")

# Function to verify the token
def verify_token(access_token: str):
    try:
        CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
        if not CLIENT_ID:
            raise ValueError("Google CLIENT_ID not found in environment variables.")
        
        # Verify the token using Google's library
        id_info = id_token.verify_oauth2_token(access_token, requests.Request(), CLIENT_ID, clock_skew_in_seconds=10)
        user_info = {
            "name": id_info.get("name"),
            "given_name": id_info.get("given_name"),
            "picture": id_info.get("picture"),
            "email": id_info.get("email")
        }

        return user_info

    except ValueError as e:
        logger.error(f"Token verification failed: {e}")
        error_message = str(e)

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_message,
        )
    
@router.post("/token")
def verify_jwt(token_data: TokenData, db: Session = Depends(get_db)):
    return verify_token(token_data.access_token, db)
