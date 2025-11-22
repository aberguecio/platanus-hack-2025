"""User model for application users."""

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base
from .associations import user_events


class User(Base):
    """User model representing application users.

    Attributes:
        id: Primary key
        telegram_id: Unique Telegram user identifier
        username: Telegram username
        first_name: User's first name
        last_name: User's last name
        phone_number: User's phone number (unique)
        created_at: Timestamp when user was created
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    phone_number = Column(String, unique=True, nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    events = relationship("Event", secondary=user_events, back_populates="users")
    memories = relationship("Memory", back_populates="user")
    conversations = relationship("Conversation", back_populates="user")
