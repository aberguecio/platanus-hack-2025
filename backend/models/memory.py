"""Memory model for storing event memories."""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from database import Base
from enums import MediaTypeEnum


class Memory(Base):
    """Memory model representing user memories within events.

    Attributes:
        id: Primary key
        event_id: Foreign key to Event
        user_id: Foreign key to User
        message_id: Optional foreign key to Message that created this memory
        text: Optional text content of the memory
        s3_url: Optional URL to media stored in S3
        media_type: Type of media (image, video, audio, text, document)
        memory_metadata: Flexible JSONB field for additional metadata
        embedding: Vector embedding for semantic search (1024 dimensions)
        created_at: Timestamp when memory was created
    """
    __tablename__ = "memories"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=True, index=True)
    text = Column(Text, nullable=True)
    s3_url = Column(String, nullable=True)
    media_type = Column(Enum(MediaTypeEnum, values_callable=lambda x: [e.value for e in x]), nullable=True)
    memory_metadata = Column(JSONB, nullable=True)
    embedding = Column(Vector(1024), nullable=True)  # Voyage AI voyage-2 embeddings are 1024 dimensionsc #TODO: Modify for improoving model.
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    event = relationship("Event", back_populates="memories")
    user = relationship("User", back_populates="memories")
    message = relationship("Message", back_populates="memories")
