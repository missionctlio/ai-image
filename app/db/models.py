from sqlalchemy import Column, String, DateTime, ForeignKey, MetaData, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from uuid import uuid4
from .database import Base

metadata = MetaData()

class User(Base):
    __tablename__ = 'users'

    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    email = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    refresh_token = Column(String, nullable=True)
    last_logged_in = Column(DateTime, server_default=func.now(), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now(), nullable=False)

    # Establish a one-to-many relationship with the Image model
    images = relationship('Image', back_populates='user', cascade='all, delete-orphan')


class Image(Base):
    __tablename__ = 'images'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    url = Column(String, nullable=False)
    description = Column(Text, nullable=True)  # Text type for longer descriptions
    prompt = Column(Text, nullable=False)  # Prompt text, cannot be null
    refinedPrompt = Column(Text, nullable=True)  # Refined prompt, can be null
    aspectRatio = Column(String, nullable=False)  # Aspect ratio, cannot be null
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    
    # Foreign key to associate the image with a user
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.uuid'), nullable=False)
    
    # Back reference to the User model
    user = relationship('User', back_populates='images')
