"""Database models for the application.

This module exports all SQLAlchemy models and association tables.
"""

from .associations import user_events
from .user import User
from .event import Event
from .memory import Memory
from .channel import Channel
from .assistant import AIMemoryAssistant
from .conversation import Conversation
from .message import Message

# Re-export enums for convenience
from enums import (
    MediaTypeEnum,
    ChannelTypeEnum,
    ConversationStatusEnum,
    MessageDirectionEnum,
)

__all__ = [
    # Association tables
    "user_events",
    # Models
    "User",
    "Event",
    "Memory",
    "Channel",
    "AIMemoryAssistant",
    "Conversation",
    "Message",
    # Enums (re-exported for backward compatibility)
    "MediaTypeEnum",
    "ChannelTypeEnum",
    "ConversationStatusEnum",
    "MessageDirectionEnum",
]
