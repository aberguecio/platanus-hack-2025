"""Channel type enumeration for multi-platform support."""

import enum


class ChannelTypeEnum(str, enum.Enum):
    """Enum for different communication channels/platforms.

    Attributes:
        TELEGRAM: Telegram messaging platform
        WHATSAPP: WhatsApp messaging platform
        WEB: Web-based interface
    """
    TELEGRAM = "telegram"
    WHATSAPP = "whatsapp"
    WEB = "web"
