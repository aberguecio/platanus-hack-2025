"""Message model for conversation history."""

from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from database import Base
from enums import MessageDirectionEnum


class Message(Base):
    """Message model representing individual messages in conversations.

    Attributes:
        id: Primary key
        conversation_id: Foreign key to Conversation
        direction: Message direction (user or assistant)
        content: Message content
        embedding: Vector embedding for semantic search (1024 dimensions)
        created_at: Timestamp when message was created
    """
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False, index=True)
    direction = Column(Enum(MessageDirectionEnum, values_callable=lambda x: [e.value for e in x]), nullable=False)
    content = Column(Text, nullable=False)
    photo_s3_url = Column(Text, nullable=True)  # S3 URL for photo attachments
    embedding = Column(Vector(1024), nullable=True)  # Voyage AI voyage-3-large embeddings are 1024 dimensions
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    memories = relationship("Memory", back_populates="message")
