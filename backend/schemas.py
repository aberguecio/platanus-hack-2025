from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enums import (
    MediaTypeEnum as MediaType,
    ChannelTypeEnum as ChannelType,
    ConversationStatusEnum as ConversationStatus,
    MessageDirectionEnum as MessageDirection,
)


class TelegramUser(BaseModel):
    """Telegram user object"""
    id: int
    is_bot: Optional[bool] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None
    language_code: Optional[str] = None


class TelegramChat(BaseModel):
    """Telegram chat object"""
    id: int
    type: Optional[str] = None
    title: Optional[str] = None
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class PhotoSize(BaseModel):
    """Telegram photo size object"""
    file_id: str
    file_unique_id: str
    width: int
    height: int
    file_size: Optional[int] = None


class TelegramMessage(BaseModel):
    """Telegram message object"""
    message_id: int
    from_: Optional[TelegramUser] = Field(None, alias="from")
    sender_chat: Optional[TelegramChat] = None
    date: int
    chat: TelegramChat
    text: Optional[str] = None
    photo: Optional[List[PhotoSize]] = None
    caption: Optional[str] = None

    class Config:
        populate_by_name = True


class TelegramUpdate(BaseModel):
    """
    Telegram update object

    This is the main object received from Telegram Bot API webhook.
    Only the most common fields are included here.

    The bot_token field is optional and not part of Telegram's standard.
    Your bot can include it when sending photos to enable image downloads.
    """
    update_id: int
    message: Optional[TelegramMessage] = None
    edited_message: Optional[TelegramMessage] = None
    channel_post: Optional[TelegramMessage] = None
    edited_channel_post: Optional[TelegramMessage] = None
    bot_token: Optional[str] = None  # Optional: include when sending photos

    class Config:
        json_schema_extra = {
            "example": {
                "update_id": 123456789,
                "message": {
                    "message_id": 1,
                    "from": {
                        "id": 123456789,
                        "is_bot": False,
                        "first_name": "Test",
                        "last_name": "User",
                        "username": "testuser"
                    },
                    "chat": {
                        "id": 123456789,
                        "first_name": "Test",
                        "last_name": "User",
                        "username": "testuser",
                        "type": "private"
                    },
                    "date": 1234567890,
                    "text": "Create event Birthday Party on 2025-12-25"
                }
            }
        }


# ============================================================================
# Database Model Schemas
# ============================================================================

# User Schemas
class UserBase(BaseModel):
    telegram_id: str
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None


class UserCreate(UserBase):
    pass


class User(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# Event Schemas
class EventBase(BaseModel):
    name: str
    description: Optional[str] = None
    event_date: Optional[datetime] = None


class EventCreate(EventBase):
    pass


class EventUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    event_date: Optional[datetime] = None
    summary: Optional[str] = None
    ai_context: Optional[str] = None


class Event(EventBase):
    id: int
    summary: Optional[str] = None
    ai_context: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Memory Schemas
class MemoryBase(BaseModel):
    event_id: int
    user_id: int
    text: Optional[str] = None
    s3_url: Optional[str] = None
    media_type: Optional[MediaType] = None
    memory_metadata: Optional[Dict[str, Any]] = None


class MemoryCreate(MemoryBase):
    message_id: Optional[int] = None


class Memory(MemoryBase):
    id: int
    message_id: Optional[int] = None
    embedding: Optional[List[float]] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Channel Schemas
class ChannelBase(BaseModel):
    name: str
    type: ChannelType
    identifier: str


class ChannelCreate(ChannelBase):
    pass


class Channel(ChannelBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# AIMemoryAssistant Schemas
class AssistantBase(BaseModel):
    personality: Optional[str] = None
    instructions: str


class AssistantCreate(AssistantBase):
    pass


class Assistant(AssistantBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# Conversation Schemas
class ConversationBase(BaseModel):
    user_id: int
    assistant_id: int
    channel_id: int
    title: Optional[str] = None
    status: ConversationStatus = ConversationStatus.ACTIVE


class ConversationCreate(ConversationBase):
    pass


class ConversationUpdate(BaseModel):
    title: Optional[str] = None
    status: Optional[ConversationStatus] = None


class Conversation(ConversationBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Message Schemas
class MessageBase(BaseModel):
    conversation_id: int
    direction: MessageDirection
    content: str


class MessageCreate(MessageBase):
    pass


class Message(MessageBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
