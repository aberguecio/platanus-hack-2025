"""Conversation model for chat threads."""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base
from enums import ConversationStatusEnum


class Conversation(Base):
    """Conversation model representing chat threads.

    Attributes:
        id: Primary key
        user_id: Foreign key to User
        assistant_id: Foreign key to AIMemoryAssistant
        channel_id: Foreign key to Channel
        title: Optional conversation title
        status: Conversation status (active, archived, deleted)
        created_at: Timestamp when conversation was created
        updated_at: Timestamp when conversation was last updated
    """
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    assistant_id = Column(Integer, ForeignKey("ai_memory_assistants.id"), nullable=False, index=True)
    channel_id = Column(Integer, ForeignKey("channels.id"), nullable=False, index=True)
    title = Column(String, nullable=True)
    status = Column(Enum(ConversationStatusEnum, values_callable=lambda x: [e.value for e in x]), nullable=False, server_default="active", index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="conversations")
    assistant = relationship("AIMemoryAssistant", back_populates="conversations")
    channel = relationship("Channel", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation")
