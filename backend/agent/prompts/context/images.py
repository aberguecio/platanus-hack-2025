"""
Image context management for conversation history.

Implements token-efficient image handling by using descriptions
instead of full base64 images in conversation history.
"""
from typing import Optional, Dict, Any


class ImageContext:
    """
    Manages image context in conversations.

    Strategy: Use descriptions instead of full images to save tokens
    - Current message: Include full image (multimodal)
    - Historical messages: Use Claude Vision descriptions only
    - Fallback: "[Foto enviada]" if description unavailable
    """

    def __init__(self, mode: str = "descriptions_only"):
        """
        Initialize image context manager.

        Args:
            mode: Image handling mode
                - "descriptions_only": Only use text descriptions (most economical)
                - "hybrid": Last N full images + descriptions for rest
                - "full": Include all images (expensive)
        """
        self.mode = mode
        self.hybrid_image_limit = 2  # If using hybrid mode

    def format_image_in_history(
        self,
        message: Dict[str, Any],
        s3_service: Optional[Any] = None
    ) -> str:
        """
        Format an image reference for conversation history.

        Args:
            message: Message dict with photo_s3_url and image_description
            s3_service: Optional S3 service (not used in descriptions_only mode)

        Returns:
            Formatted string representation of the image
        """
        if self.mode == "descriptions_only":
            return self._format_as_description(message)
        elif self.mode == "hybrid":
            # TODO: Implement hybrid mode (last N images full, rest descriptions)
            return self._format_as_description(message)
        elif self.mode == "full":
            # TODO: Implement full image retrieval from S3
            return self._format_as_description(message)
        else:
            return self._format_as_description(message)

    def _format_as_description(self, message: Dict[str, Any]) -> str:
        """
        Format image as text description.

        Uses Claude Vision generated description if available,
        falls back to generic placeholder.
        """
        description = message.get("image_description", "")
        content = message.get("content", "")

        if description:
            # Use the AI-generated description
            if content:
                return f"[Foto: {description}]\n{content}"
            else:
                return f"[Foto: {description}]"
        else:
            # Fallback to generic placeholder
            if content:
                return f"[Foto enviada]\n{content}"
            else:
                return "[Foto enviada]"

    def should_include_full_image(
        self,
        message_position: int,
        total_messages: int
    ) -> bool:
        """
        Determine if a message should include the full image.

        Used in hybrid mode to decide which images get full inclusion.

        Args:
            message_position: Position of message in history (0 = oldest)
            total_messages: Total number of messages

        Returns:
            True if should include full image, False for description only
        """
        if self.mode == "full":
            return True
        elif self.mode == "descriptions_only":
            return False
        elif self.mode == "hybrid":
            # Include only last N images
            recent_threshold = total_messages - self.hybrid_image_limit
            return message_position >= recent_threshold
        else:
            return False

    def estimate_tokens(self, mode: str, num_images: int) -> int:
        """
        Estimate token cost for different image modes.

        Rough estimates:
        - Description only: ~50-150 tokens per image
        - Full image: ~85 base + ~5.78 per 512px tile (variable)

        Args:
            mode: Image handling mode
            num_images: Number of images in context

        Returns:
            Estimated token count
        """
        if mode == "descriptions_only":
            return num_images * 100  # Average description length

        elif mode == "hybrid":
            full_images = min(num_images, self.hybrid_image_limit)
            description_images = num_images - full_images
            return (full_images * 500) + (description_images * 100)  # Conservative estimate

        elif mode == "full":
            return num_images * 500  # Conservative per-image estimate

        return 0
