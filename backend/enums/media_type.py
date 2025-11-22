"""Media type enumeration for memory content types."""

import enum


class MediaTypeEnum(str, enum.Enum):
    """Enum for different types of media in memories.

    Attributes:
        IMAGE: Photo or image files
        VIDEO: Video files
        AUDIO: Audio files or voice messages
        TEXT: Pure text memories without media
        DOCUMENT: PDF, documents, and other file types
    """
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    TEXT = "text"
    DOCUMENT = "document"
