"""Channel model for multi-platform support."""

from sqlalchemy import Column, Integer, String, DateTime, Enum, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base
from enums import ChannelTypeEnum


class Channel(Base):
    """Channel model representing communication platforms.

    Attributes:
        id: Primary key
        name: Channel name (e.g., "Main Telegram Bot")
        type: Channel platform type (telegram, whatsapp, web)
        identifier: Unique identifier for the channel (e.g., bot token)
        created_at: Timestamp when channel was created
    """
    __tablename__ = "channels"
    __table_args__ = (
        UniqueConstraint('type', 'identifier', name='unique_channel_type_identifier'),
    )

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    type = Column(Enum(ChannelTypeEnum), nullable=False, index=True)
    identifier = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    conversations = relationship("Conversation", back_populates="channel")
