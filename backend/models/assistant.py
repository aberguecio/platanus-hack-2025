"""AI Memory Assistant model for different AI personalities."""

from sqlalchemy import Column, Integer, Text, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base


class AIMemoryAssistant(Base):
    """AI Memory Assistant model for configurable AI personalities.

    Attributes:
        id: Primary key
        personality: Optional personality description for the assistant
        instructions: System instructions for the assistant
        created_at: Timestamp when assistant was created
    """
    __tablename__ = "ai_memory_assistants"

    id = Column(Integer, primary_key=True, index=True)
    personality = Column(Text, nullable=True)
    instructions = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    conversations = relationship("Conversation", back_populates="assistant")
