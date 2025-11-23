from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from dataclasses import dataclass, field


@dataclass
class ExecutionContext:
    """Context object containing all dependencies needed for tool execution"""

    # Core dependencies
    db: Session
    user: Any

    # External services (optional, depending on the tool)
    s3_service: Optional[Any] = None
    telegram_service: Optional[Any] = None
    image_service: Optional[Any] = None

    # Request metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Conversation context
    conversation_id: Optional[int] = None
    conversation_history: Optional[List[Dict[str, str]]] = None

    # Batch processing support
    is_batch: bool = False
    batch_photos: List[Dict[str, Any]] = field(default_factory=list)
    batch_message_ids: List[int] = field(default_factory=list)

    # Convenient properties to access common metadata
    @property
    def telegram_id(self) -> Optional[str]:
        return self.metadata.get("telegram_id")

    @property
    def username(self) -> Optional[str]:
        return self.metadata.get("username")

    @property
    def first_name(self) -> Optional[str]:
        return self.metadata.get("first_name")

    @property
    def last_name(self) -> Optional[str]:
        return self.metadata.get("last_name")

    @property
    def has_photo(self) -> bool:
        return self.metadata.get("has_photo", False)

    @property
    def photo_file_id(self) -> Optional[str]:
        return self.metadata.get("photo_file_id")

    @property
    def has_video(self) -> bool:
        return self.metadata.get("has_video", False)

    @property
    def video_file_id(self) -> Optional[str]:
        return self.metadata.get("video_file_id")

    @property
    def message_id(self) -> Optional[int]:
        return self.metadata.get("message_id")


class BaseTool(ABC):
    """Base abstract class for all agent tools"""

    def __init__(self, name: str, description: str, input_schema: dict):
        self.name = name
        self.description = description
        self.input_schema = input_schema

    @abstractmethod
    async def execute(
        self, tool_input: Dict[str, Any], ctx: ExecutionContext
    ) -> Dict[str, Any]:
        """
        Execute the tool with the given input and execution context

        Args:
            tool_input: The input parameters for the tool
            ctx: Execution context with db, user, services, and metadata

        Returns:
            Dict with format: {"success": bool, "message": str, ...additional_data}
        """
        pass

    def to_schema(self) -> Dict[str, Any]:
        """Convert tool to Anthropic API format"""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
        }
