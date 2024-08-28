from fastapi import APIRouter, Depends, Header, HTTPException, status, Response
from pydantic import BaseModel
from google.oauth2 import id_token
from google.auth.transport import requests
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import User
from datetime import datetime, timezone, timedelta
import requests as req
import redis
import jwt
import uuid
import logging
import os

# Initialize Redis connection
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)

router = APIRouter()

# Logger configuration
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Environment variables
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
JWT_SECRET = os.getenv("JWT_SECRET", "your_jwt_secret")
JWT_ALGORITHM = "HS256"
JWT_ACCESS_EXPIRE_MINUTES = 15
JWT_REFRESH_EXPIRE_DAYS = 30

class TokenData(BaseModel):
    access_token: str

class RefreshTokenData(BaseModel):
    refresh_token: str

class TokenResponse(BaseModel):
    user_info: dict

def verify_token(access_token: str, db: Session):
    logger.info("Starting token verification")
    try:
        if not GOOGLE_CLIENT_ID:
            logger.error("Google CLIENT_ID not found in environment variables.")
            raise ValueError("Google CLIENT_ID not found in environment variables.")
        
        # Verify the token using Google's library
        id_info = id_token.verify_oauth2_token(access_token, requests.Request(), GOOGLE_CLIENT_ID, clock_skew_in_seconds=10)
        logger.info("Token verified successfully")

        # Extract user info
        user_info = {
            "name": id_info.get("name"),
            "given_name": id_info.get("given_name"),
            "picture": id_info.get("picture"),
            "email": id_info.get("email")
        }

        find_or_create_user(email=user_info["email"], name=user_info["name"],db=db)

        return user_info

    except ValueError as e:
        logger.error(f"Token verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token"
        )

def find_or_create_user(email: str, name: str, db: Session) -> User:
    logger.debug(f"Finding or creating user with email: {email}")
    
    # Check if the user exists in the database
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        logger.info(f"User not found. Creating new user with email: {email}")
        user = User(
            uuid=uuid.uuid4(),
            email=email,
            name=name,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            refresh_token=None  # Initialize with None or appropriate default
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info(f"New user created with UUID: {user.uuid}, email: {email}")
    else:
        logger.info(f"User {user.email} found")

    return user

def get_current_user(authorization: str = Header(None), db: Session = Depends(get_db), response: Response = None):
    logger.info("Extracting current user from authorization header")
    if authorization:
        token = authorization.split("Bearer ")[-1]
        try:
            # Verify the access token and get user info
            user_info = verify_token(token, db)
            email = user_info['email']
            name = user_info.get('given_name', 'Unknown')

            # Check Redis cache
            cached_user = redis_client.get(f"user:{email}")
            if cached_user:
                logger.info(f"User found in cache: {email}")
                return user_info

            # Find or create the user in the database
            user = find_or_create_user(email, name, db)

            # Check if refresh token needs to be updated
            if user.refresh_token:
                google_refresh_token = user.refresh_token
                # Try refreshing the token
                new_tokens = refresh_google_tokens(google_refresh_token)
                if new_tokens:
                    user.refresh_token = new_tokens['refresh_token']
                    db.commit()
                    logger.info(f"Updated user refresh token in database")

                    # Set new tokens in HTTP-only cookies
                    if response:
                        response.set_cookie(key="access_token", value=new_tokens['access_token'], httponly=True, secure=True)
                        response.set_cookie(key="refresh_token", value=new_tokens['refresh_token'], httponly=True, secure=True)
                        logger.info("Set new tokens in HTTP-only cookies")

            # Cache the user info
            redis_client.setex(f"user:{email}", 600, str(user_info))  # Cache for 10 minutes
            logger.info(f"Cached user info for email: {email}")

            return user_info

        except HTTPException as e:
            logger.error(f"Authentication failed: {e.detail}")
            raise e
    logger.error("Authorization token is required")
    raise HTTPException(status_code=401, detail="Authorization token is required")

def generate_jwt(user_info: dict, refresh_token: str = None) -> str:
    logger.info("Generating JWT")
    expire = datetime.utcnow() + timedelta(minutes=JWT_ACCESS_EXPIRE_MINUTES)
    to_encode = user_info.copy()
    to_encode.update({"exp": expire, "refresh_token": refresh_token})
    jwt_token = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    logger.info(f"JWT generated with expiration: {expire}")
    return jwt_token

def get_existing_refresh_token(email: str, db: Session) -> str:
    logger.info(f"Fetching existing refresh token for email: {email}")
    user = db.query(User).filter(User.email == email).first()
    if user:
        if user.refresh_token:
            logger.info(f"Found existing refresh token for email: {email}")
            return user.refresh_token
        else:
            logger.info(f"No refresh token found for email: {email}")
            return None
    else:
        logger.error(f"User not found for email: {email}, skipping.")
        return None

def refresh_google_tokens(refresh_token: str) -> dict:
    logger.info("Refreshing Google tokens")
    response = req.post(
        "https://oauth2.googleapis.com/token",
        data={
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
            "refresh_token": refresh_token,
            "access_type": "offline",
            "grant_type": "refresh_token"
        }
    )
    response_data = response.json()
    if response.status_code == 200:
        logger.info("Google tokens refreshed successfully")
        return response_data
    else:
        logger.error(f"Failed to refresh Google tokens, status code: {response.status_code}, response: {response_data}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Failed to refresh Google tokens"
        )

@router.post("/token", response_model=TokenResponse)
def verify_jwt(response: Response, authorization: str = Header(None), db: Session = Depends(get_db)):
    logger.info("Verifying JWT")
    if not authorization or not authorization.startswith("Bearer "):
        logger.error("Authorization header missing or incorrect")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing or incorrect"
        )

    # Extract the Google token from the Authorization header
    google_token = authorization.split("Bearer ")[1]
    logger.info 
    refresh_code = exchange_code(google_token)
    print(f"{refresh_code}")
    try:
        # Verify the Google token and get user info
        user_info = verify_token(google_token, db)
        email = user_info['email']
        refresh_token = get_existing_refresh_token(email, db)

        if not refresh_token:
            # If the user does not have a refresh token, generate one and save it
            user = db.query(User).filter(User.email == email).first()
            if user:
                # Generate new refresh token
                google_tokens = refresh_google_tokens(google_token)
                new_refresh_token = google_tokens.get("refresh_token")
                user.refresh_token = new_refresh_token
                db.commit()
                logger.info(f"Updated user's refresh token in the database for email: {email}")

                refresh_token = new_refresh_token

        # Generate a new JWT
        jwt_token = generate_jwt(user_info, refresh_token)

        # Set the JWT as an HTTP-only cookie
        response.set_cookie(
            key="access_token",
            value=jwt_token,
            httponly=True,
            secure=True,
            samesite='Lax'
        )
        logger.info(f"JWT set in HTTP-only cookie for user: {email}")

        return TokenResponse(
            access_token=jwt_token,
            refresh_token=refresh_token,
            user_info=user_info
        )

    except HTTPException as e:
        logger.error(f"Token verification failed: {e.detail}")
        raise e
def exchange_code(code: str):
    logger.info("Exchanging authorization code for tokens")

    try:
        response = req.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": "https://dev.aesync.com"  # Use the redirect URI you registered
            }
        )
        response_data = response.json()
        
        if response.status_code == 200:
            logger.info(f"Tokens exchanged successfully, response: {response_data}")
            return response_data
        else:
            logger.error(f"Failed to exchange code, status code: {response.status_code}, response: {response_data}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to exchange authorization code for tokens"
            )
    except Exception as e:
        logger.error(f"Exception occurred: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while exchanging the authorization code"
        )    

@router.post("/refresh", response_model=TokenResponse)
def refresh_token(refresh_token_data: RefreshTokenData, response: Response, db: Session = Depends(get_db)):
    logger.info("Refreshing token")
    try:
        # Refresh Google tokens
        google_tokens = refresh_google_tokens(refresh_token_data.refresh_token)
        new_refresh_token = google_tokens.get("refresh_token")
        new_access_token = google_tokens.get("access_token")
        
        user_info = verify_token(new_access_token)
        email = user_info['email']
        
        # Update user's refresh token in the database
        user = db.query(User).filter(User.email == email).first()
        if user:
            user.refresh_token = new_refresh_token
            user.updated_at = datetime.now(timezone.utc)
            db.commit()
            logger.info(f"Updated user's refresh token in the database for email: {email}")

            # Generate new JWT
            jwt_token = generate_jwt(user_info, new_refresh_token)

            response.set_cookie(
                key="access_token",
                value=jwt_token,
                httponly=True,
                secure=True,
                samesite='Lax'
            )
            logger.info(f"JWT set in HTTP-only cookie for user: {email}")

            return TokenResponse(
                access_token=jwt_token,
                refresh_token=new_refresh_token,
                user_info=user_info
            )
        else:
            logger.error(f"User not found for email: {email}")
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )
    
    except HTTPException as e:
        logger.error(f"Token refresh failed: {e.detail}")
        raise e
