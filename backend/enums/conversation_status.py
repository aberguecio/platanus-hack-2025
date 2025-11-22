"""Conversation status enumeration for tracking conversation lifecycle."""

import enum


class ConversationStatusEnum(str, enum.Enum):
    """Enum for conversation lifecycle states.

    Attributes:
        ACTIVE: Conversation is currently active
        ARCHIVED: Conversation has been archived by user
        DELETED: Conversation has been soft-deleted
    """
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"
