from sqlalchemy.orm import Session
from app.db.models import User
from app.db.schemas.user import UserCreate, UserUpdate
from uuid import UUID

def get_user(db: Session, user_uuid: UUID):
    return db.query(User).filter(User.uuid == user_uuid).first()

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def get_users(db: Session, skip: int = 0, limit: int = 10):
    return db.query(User).offset(skip).limit(limit).all()

def create_user(db: Session, user: UserCreate):
    db_user = User(email=user.email, name=user.name)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user(db: Session, user_uuid: UUID, user: UserUpdate):
    db_user = db.query(User).filter(User.uuid == user_uuid).first()
    if db_user:
        for key, value in user.dict(exclude_unset=True).items():
            setattr(db_user, key, value)
        db.commit()
        db.refresh(db_user)
    return db_user

def delete_user(db: Session, user_uuid: UUID):
    db_user = db.query(User).filter(User.uuid == user_uuid).first()
    if db_user:
        db.delete(db_user)
        db.commit()
    return db_user
def get_user_from_uuid(user_uuid: str, db: Session) -> User:
    """Fetch user from the database by UUID."""
    return db.query(User).filter(User.uuid == user_uuid).first()