from pydantic import BaseModel, Field
from typing import Optional, List


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
