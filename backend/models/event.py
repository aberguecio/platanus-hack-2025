"""Event model for organizing memories."""

from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base
from .associations import user_events
import secrets
import string

def generate_invite_code() -> str:
    """
    Generate a unique, URL-safe invite code for events.

    Format: evt_<16 random alphanumeric characters>
    Example: evt_a1b2c3d4e5f6g7h8

    Why this format:
    - 'evt_' prefix makes it human-readable and reduces collision with other codes
    - 16 alphanumeric chars = ~95 bits of entropy
    - Probability of collision with 1M events: ~1e-18
    - URL-safe (no special characters)
    """
    alphabet = string.ascii_lowercase + string.digits
    random_part = ''.join(secrets.choice(alphabet) for _ in range(16))
    return f"evt_{random_part}"


class Event(Base):
    """Event model representing memory collection events.

    Attributes:
        id: Primary key
        name: Event name
        description: Event description
        event_date: Date when the event occurred/will occur
        summary: AI-generated summary of the event
        ai_context: AI context for understanding the event
        created_at: Timestamp when event was created
    """
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    event_date = Column(DateTime(timezone=True), nullable=True)
    invite_code = Column(String(20), unique=True, index=True, nullable=False, default=generate_invite_code)
    summary = Column(Text, nullable=True)
    ai_context = Column(Text, nullable=True)
    generated_narrative = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    users = relationship("User", secondary=user_events, back_populates="events")
    memories = relationship("Memory", back_populates="event")
