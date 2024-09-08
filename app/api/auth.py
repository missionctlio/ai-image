from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import User
from app.db.model.user import get_user_from_uuid
from datetime import datetime, timezone, timedelta
import uuid
import logging
import os
from jose import JWTError, jwt
from google.oauth2 import id_token
from google.auth.transport import requests
import time

# Set up logging configuration
logging = logging.getLogger(__name__)

router = APIRouter()


# Constants from environment variables
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 30))
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
if not GOOGLE_CLIENT_ID:
    raise ValueError("Google CLIENT_ID not found in environment variables.")

# Calculate max age in seconds
ACCESS_TOKEN_MAX_AGE_SECONDS = ACCESS_TOKEN_EXPIRE_MINUTES * 60
REFRESH_TOKEN_MAX_AGE_SECONDS = REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60

class TokenData(BaseModel):
    access_token: str

def create_jwt_token(data: dict, expires_delta: timedelta):
    expire = datetime.utcnow() + expires_delta
    data.update({"exp": expire})
    encoded_jwt = jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)
    logging.info(f"Created JWT token with expiry {expire} and data {data}")
    return encoded_jwt

def generate_tokens(user: User):
    token_data = {
        "sub": str(user.uuid), 
        "email": user.email, 
        "name": user.name
    }
    access_token = create_jwt_token(token_data, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    refresh_token = create_jwt_token(token_data, timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))
    logging.info(f"Tokens generated for user with email {user.email}")
    return access_token, refresh_token

def validate_jwt_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if "sub" not in payload:
            logging.error(f"Token validation failed: 'sub' claim missing for token {token}")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        logging.info(f"JWT token validated successfully for email {payload.get('email')}")
        return payload
    except JWTError as e:
        logging.error(f"Token validation failed with error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

async def get_current_user(request: Request, db: Session = Depends(get_db)):
    access_token = request.cookies.get("access_token")
    if access_token:
        try:
            payload = validate_jwt_token(access_token)
            user_uuid = payload.get("sub")
            user = get_user_from_uuid(user_uuid, db)
            if not user:
                logging.error(f"User not found with email {payload.get('email')}")
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
            return user
        except HTTPException:
            logging.warning(f"Access token invalid or expired for token {access_token}")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token Expired")
    logging.warning("Access token missing or invalid, attempting refresh")
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token missing or invalid")

@router.post("/refresh")
async def refresh_access_token(request: Request, db: Session = Depends(get_db)):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        logging.error("Refresh token missing")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token missing")
    try:
        payload = validate_jwt_token(refresh_token)
        user_uuid = payload.get("sub")
        user = get_user_from_uuid(user_uuid, db)
        if not user:
            logging.error(f"User not found during refresh for UUID {user_uuid}")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        new_access_token, _ = generate_tokens(user)
        response = Response()
        response.set_cookie(
            key="access_token",
            value=new_access_token,
            httponly=True,
            secure=True,
            max_age=ACCESS_TOKEN_MAX_AGE_SECONDS,
            samesite="None",
            path="/"  # Ensure the cookie is available site-wide
        )
        logging.info(f"Access token refreshed and set in cookies for user with email {payload.get('email')}")
        return response
    except JWTError:
        logging.error(f"Invalid refresh token: {refresh_token}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

@router.post("/token")
def verify_token(token_data: TokenData, response: Response, db: Session = Depends(get_db)):
    response.headers["Access-Control-Allow-Origin"] = "*"
    user_info = verify_google_oauth_token(token_data.access_token)
    user = db.query(User).filter(User.email == user_info["email"]).first()
    if not user:
        user = User(
            uuid=uuid.uuid4(),
            email=user_info["email"],
            name=user_info["name"],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            refresh_token=None  # You might want to initialize this appropriately
        )
        db.add(user)
    access_token, refresh_token = generate_tokens(user)
    user.refresh_token = refresh_token
    db.commit()
    response.set_cookie(
        key="access_token", value=access_token, httponly=True, secure=True, max_age=ACCESS_TOKEN_MAX_AGE_SECONDS, samesite="None"
    )
    response.set_cookie(
        key="refresh_token", value=refresh_token, httponly=True, secure=True, max_age=REFRESH_TOKEN_MAX_AGE_SECONDS, samesite="None"
    )
    return {"userInfo": user_info, "accessToken": access_token}

def verify_google_oauth_token(access_token: str):
    try:
        id_info = id_token.verify_oauth2_token(access_token, requests.Request(), GOOGLE_CLIENT_ID, clock_skew_in_seconds=10)
        if id_info.get("exp") < time.time():
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
        return id_info
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    

@router.get("/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response):
    """
    Logs out the user by deleting the access_token and refresh_token cookies.
    """
    # Delete the access_token cookie
    response.delete_cookie(key="access_token", httponly=True)

    # Delete the refresh_token cookie
    response.delete_cookie(key="refresh_token", httponly=True)

    return {"detail": "Logged out successfully"}