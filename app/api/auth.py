from fastapi import APIRouter, Depends, Header, HTTPException, status, Response, Request
from pydantic import BaseModel
from google.oauth2 import id_token
from google.auth.transport import requests
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import User  # Adjust this import based on your directory structure
from datetime import datetime, timezone, timedelta
import uuid
import logging
import time
import os
from jose import JWTError, jwt

router = APIRouter()

# Logger configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 30

class TokenData(BaseModel):
    access_token: str

def create_jwt_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    logger.info(f"Created JWT token with expiry: {expire}")
    return encoded_jwt

def generate_tokens(user_info: dict):
    logger.info("Generating new access and refresh tokens")
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    access_token = create_jwt_token(
        data={"sub": user_info["email"], "name": user_info["name"], "photo": user_info["picture"]},
        expires_delta=access_token_expires
    )
    refresh_token = create_jwt_token(
        data={"sub": user_info["email"]},
        expires_delta=refresh_token_expires
    )
    
    logger.info(f"Generated access token: {access_token}")
    logger.info(f"Generated refresh token: {refresh_token}")
    return access_token, refresh_token

def validate_jwt_token(token: str):
    logger.info(f"Validating JWT token: {token}")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            logger.error("Token payload does not contain 'sub'")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        logger.info(f"Token validated successfully for email: {email}")
        return payload
    except JWTError as e:
        logger.error(f"Token validation failed: {e}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

async def get_current_user(request: Request, db: Session = Depends(get_db)):
    logger.info("Fetching current user")
    access_token = request.cookies.get("access_token")
    refresh_token = request.cookies.get("refresh_token")

    email = None  # Initialize email

    if not access_token:
        logger.error("Access token missing in cookies")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Access token missing")

    # Validate the access token
    try:
        token_data = validate_jwt_token(access_token)
        logger.info(f"Access token validated successfully {access_token}")
        email = token_data.get("sub")
        logger.info(f"Access token validated, email extracted: {email}")
    except HTTPException:
        logger.info("Access token invalid, attempting to refresh")
        if not refresh_token:
            logger.error("Refresh token missing in cookies")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token missing")

        try:
            # Validate the refresh token
            validate_jwt_token(refresh_token)
            logger.info("Refresh token validated successfully")

            # Attempt to find or create the user
            user = db.query(User).filter(User.email == email).first()
            if not user:
                logger.info(f"User with email {email} not found, creating new user")
                user = User(
                    uuid=uuid.uuid4(),
                    email=email,
                    name="Unknown",  # Default values, should be updated later
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                    refresh_token=refresh_token
                )
                db.add(user)
                db.commit()
                logger.info(f"New user created with email {email}")
            else:
                logger.info(f"User with email {email} found")

            new_access_token, _ = generate_tokens({"email": user.email, "name": user.name, "picture": user.photo})
            response = Response()
            response.set_cookie(
                key="access_token", value=f"{new_access_token}", httponly=True, secure=True, max_age=60*60
            )
            logger.info(f"New access token set in cookies")
            return user

        except HTTPException:
            logger.error("Invalid refresh token")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    # Retrieve user from the database
    if email:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            logger.error(f"User with email {email} not found")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        logger.info(f"User {user.email} found")
        return user
    else:
        logger.error("Invalid access token, no email found")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token")

@router.post("/token")
def verify_token(token_data: TokenData, response: Response, db: Session = Depends(get_db)):
    logger.info("Verifying token and generating new tokens")
    # Verify the Google OAuth token
    user_info = verify_google_oauth_token(token_data.access_token)
    logger.info(f"Google OAuth token verified, user info: {user_info}")
    
    # Generate JWT and refresh tokens
    access_token, refresh_token = generate_tokens(user_info)
    
    logger.info(f"Generated new access and refresh tokens")
    
    # Store refresh token in the user record
    user = db.query(User).filter(User.email == user_info["email"]).first()
    if not user:
        logger.info(f"Creating new user with email {user_info['email']}")
        user = User(
            uuid=uuid.uuid4(),
            email=user_info["email"],
            name=user_info["name"],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            refresh_token=refresh_token
        )
        db.add(user)
    else:
        logger.info(f"Updating refresh token for existing user {user_info['email']}")
        user.refresh_token = refresh_token

    db.commit()
    logger.info(f"User record updated with new refresh token")

    # Set tokens as HTTP-only secure cookies
    response.set_cookie(
        key="access_token", value=f"{access_token}", httponly=True, secure=True, max_age=60*60
    )
    response.set_cookie(
        key="refresh_token", value=refresh_token, httponly=True, secure=True, max_age=60*60*24*30
    )
    logger.info("Set new access and refresh tokens in cookies")

    return {"userInfo": user_info, "accessToken": access_token}

def verify_google_oauth_token(access_token: str):
    logger.info(f"Verifying Google OAuth token: {access_token}")
    try:
        CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
        if not CLIENT_ID:
            logger.error("Google CLIENT_ID not found in environment variables")
            raise ValueError("Google CLIENT_ID not found in environment variables.")
        
        # Verify the token using Google's library
        id_info = id_token.verify_oauth2_token(access_token, requests.Request(), CLIENT_ID, clock_skew_in_seconds=10)
        
        # Check if the token has expired
        if id_info.get("exp") < time.time():
            logger.error("Google OAuth token has expired")
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
        logger.info(f"Google OAuth token verified successfully, user info: {user_info}")

        return user_info

    except ValueError as e:
        logger.error(f"Google OAuth token verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e)
