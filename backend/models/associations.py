"""Association tables for many-to-many relationships."""

from sqlalchemy import Column, Integer, ForeignKey, DateTime, Table
from sqlalchemy.sql import func
from database import Base


# Many-to-many relationship table between User and Event
user_events = Table(
    'user_events',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('event_id', Integer, ForeignKey('events.id'), primary_key=True),
    Column('joined_at', DateTime(timezone=True), server_default=func.now())
)
