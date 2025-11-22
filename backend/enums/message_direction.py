"""Message direction enumeration for tracking message sender."""

import enum


class MessageDirectionEnum(str, enum.Enum):
    """Enum for message direction in conversations.

    Attributes:
        USER: Message sent by the user
        ASSISTANT: Message sent by the AI assistant
    """
    USER = "user"
    ASSISTANT = "assistant"
