from fastapi import Request, HTTPException, Depends
from pydantic import BaseModel
import jwt
import os
from datetime import datetime, timedelta

# Load the secret key from environment variables
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your_secret_key")
ALGORITHM = "HS256"  # Define the algorithm used for encoding and decoding
ACCESS_TOKEN_EXPIRE_MINUTES = 30  # Set the default token expiration time

class TokenData(BaseModel):
    username: str

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

def verify_token(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(status_code=401, detail="Token missing")
    
    try:
        token = auth_header.split(" ")[1]  # Extract the token from "Bearer <token>"
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return TokenData(username=username)
    except IndexError:
        raise HTTPException(status_code=401, detail="Invalid token format")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
