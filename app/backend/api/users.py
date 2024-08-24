from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi_jwt_auth import AuthJWT
import uuid
from datetime import datetime, timezone
from typing import List
from uuid import UUID
from app.db.models import User  # Adjusted path for the User model
from app.db.schemas.user import UserCreate, UserRead  # Adjusted path for schemas
from app.db.database import get_db  # Adjusted path for the get_db function

router = APIRouter()

# Route to list all users, protected by JWT
@router.get("/", response_model=List[UserRead])
def list_users(skip: int = 0, limit: int = 10, db: Session = Depends(get_db), Authorize: AuthJWT = Depends()):
    Authorize.jwt_required()  # Require valid JWT for this route
    users = db.query(User).offset(skip).limit(limit).all()
    return users

# Route to create a new user, protected by JWT
@router.post("/", response_model=UserRead)
def create_user(user: UserCreate, db: Session = Depends(get_db), Authorize: AuthJWT = Depends()):
    Authorize.jwt_required()  # Require valid JWT for this route
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    new_user = User(
        uuid=uuid.uuid4(),
        email=user.email,
        name=user.name,
        updated_at=datetime.now(timezone.utc),
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

# Route to read a specific user, protected by JWT
@router.get("/{user_id}", response_model=UserRead)
def read_user(user_id: UUID, db: Session = Depends(get_db), Authorize: AuthJWT = Depends()):
    Authorize.jwt_required()  # Require valid JWT for this route
    user = db.query(User).filter(User.uuid == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# Route to update a user, protected by JWT
@router.put("/{user_id}", response_model=UserRead)
def update_user(user_id: UUID, updated_user: UserCreate, db: Session = Depends(get_db), Authorize: AuthJWT = Depends()):
    Authorize.jwt_required()  # Require valid JWT for this route
    user = db.query(User).filter(User.uuid == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    user.email = updated_user.email
    user.name = updated_user.name
    db.commit()
    db.refresh(user)
    return user

# Route to delete a user, protected by JWT
@router.delete("/{user_id}", response_model=UserRead)
def delete_user(user_id: UUID, db: Session = Depends(get_db), Authorize: AuthJWT = Depends()):
    Authorize.jwt_required()  # Require valid JWT for this route
    user = db.query(User).filter(User.uuid == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return user
