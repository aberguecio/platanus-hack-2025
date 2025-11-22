"""Message model for conversation history."""

from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base
from enums import MessageDirectionEnum


class Message(Base):
    """Message model representing individual messages in conversations.

    Attributes:
        id: Primary key
        conversation_id: Foreign key to Conversation
        direction: Message direction (user or assistant)
        content: Message content
        created_at: Timestamp when message was created
    """
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False, index=True)
    direction = Column(Enum(MessageDirectionEnum), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    memories = relationship("Memory", back_populates="message")
