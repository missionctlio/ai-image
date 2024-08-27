from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel
from google.oauth2 import id_token
from google.auth.transport import requests
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import User  # Adjust this import based on your directory structure
from datetime import datetime, timezone
import uuid
import logging
import os

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
            user_info = verify_token(token, db)  # Verify the token
            return user_info
        except HTTPException as e:
            logger.error(f"Authentication failed: {e.detail}")
            raise HTTPException(status_code=e.status_code, detail=e.detail)
    raise HTTPException(status_code=401, detail="Authorization token is required")


# Function to verify the token
def verify_token(access_token: str, db: Session = Depends(get_db)):
    try:
        # Specify the CLIENT_ID of the app that accesses the backend
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

        # The token is valid. Extract user information if needed.
        email = user_info['email']
        name = user_info.get('given_name', 'Unknown')  # Use 'Unknown' as a default value if 'given_name' is not present
        
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
            logger.info(f"New user created with UUID: {user.uuid}, {id_info}")
        else:
            logger.info(f"User {user.email} found, verifying token")
    
        return user_info
    except ValueError as e:
        # Log the detailed error message
        logger.error(f"Token verification failed: {e}")
        
        # Extract the error detail from the exception
        error_message = str(e)

        # Map common errors to specific HTTP responses if needed
        if 'token expired' in error_message:
            detail = "Token has expired"
        elif 'token malformed' in error_message:
            detail = "Token is malformed"
        elif 'token revoked' in error_message:
            detail = "Token has been revoked"
        else:
            detail = "Invalid token"

        # Raise an HTTP exception with a descriptive detail message
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_message,
        )
    
@router.post("/token")
def verify_jwt(token_data: TokenData, db: Session = Depends(get_db)):
    return verify_token(token_data.access_token, db)
