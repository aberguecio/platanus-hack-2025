import os
import base64
import logging
from typing import Optional
from anthropic import Anthropic
from .telegram import TelegramService
from .s3 import S3Service
from .prompts import IMAGE_DESCRIPTION_DEFAULT_PROMPT

logger = logging.getLogger(__name__)

class ImageService:
    """Service for image processing and description generation"""

    def __init__(
        self,
        telegram_service: Optional[TelegramService] = None,
        s3_service: Optional[S3Service] = None
    ):
        """
        Initialize ImageService with dependencies.

        Args:
            telegram_service: Service for downloading images from Telegram
            s3_service: Service for storing images in S3 (optional)
        """
        self.telegram_service = telegram_service
        self.s3_service = s3_service

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")
        self.claude_client = Anthropic(api_key=api_key)
        self.vision_model = "claude-haiku-4-5-20251001" 

    async def download_telegram_photo(self, file_id: str) -> bytes:
        """
        Download a photo from Telegram.

        Args:
            file_id: Telegram file_id for the photo

        Returns:
            Image bytes
        """
        if not self.telegram_service:
            raise ValueError("TelegramService not initialized")

        try:
            image_bytes = await self.telegram_service.download_file(file_id)
            logger.info(f"Downloaded image from Telegram (file_id: {file_id})")
            return image_bytes
        except Exception as e:
            logger.error(f"Failed to download image from Telegram: {e}")
            raise

    async def store_image_s3(self, image_bytes: bytes, filename: str) -> Optional[str]:
        """
        Store image in S3.

        Args:
            image_bytes: Image data
            filename: Filename to store as

        Returns:
            S3 URL if successful, None if S3 not configured or failed
        """
        if not self.s3_service:
            logger.warning("S3Service not initialized, skipping S3 storage")
            return None

        try:
            s3_url = await self.s3_service.upload_file(image_bytes, filename)
            logger.info(f"Uploaded image to S3: {s3_url}")
            return s3_url
        except Exception as e:
            logger.error(f"Failed to upload image to S3: {e}")
            return None

    def describe_image(
        self,
        image_bytes: bytes,
        custom_prompt: Optional[str] = None,
        max_tokens: int = 1024
    ) -> str:
        """
        Generate a detailed description of an image using Claude Vision.

        Args:
            image_bytes: Image data (JPEG, PNG, WebP, or GIF)
            custom_prompt: Custom prompt for description (optional)
            max_tokens: Maximum tokens for description

        Returns:
            Text description of the image
        """
        # Encode image to base64
        base64_image = base64.standard_b64encode(image_bytes).decode("utf-8")

        # Detect image format (simple heuristic based on magic bytes)
        media_type = self._detect_image_format(image_bytes)

        prompt = custom_prompt or IMAGE_DESCRIPTION_DEFAULT_PROMPT


        try:
            # Call Claude Vision API
            message = self.claude_client.messages.create(
                model=self.vision_model,
                max_tokens=max_tokens,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": base64_image,
                                },
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ],
                    }
                ],
            )


            # Extract text response
            description = message.content[0].text
            logger.info(f"Generated image description ({len(description)} chars)")

            return description

        except Exception as e:
            logger.error(f"Failed to generate image description: {e}")
            raise

    async def process_telegram_photo(
        self,
        file_id: str,
        store_in_s3: bool = False,
        custom_prompt: Optional[str] = None
    ) -> tuple[str, Optional[str]]:
        """
        Complete workflow: download, describe, and optionally store a Telegram photo.

        Args:
            file_id: Telegram file_id
            store_in_s3: Whether to store in S3
            custom_prompt: Custom prompt for description

        Returns:
            Tuple of (description, s3_url)
            s3_url will be None if not stored or S3 not configured
        """
        # Download image
        image_bytes = await self.download_telegram_photo(file_id)

        # Generate description
        description = self.describe_image(image_bytes, custom_prompt)

        # Optionally store in S3
        s3_url = None
        if store_in_s3:
            filename = f"memory_{file_id}.jpg"
            s3_url = await self.store_image_s3(image_bytes, filename)

        return description, s3_url

    @staticmethod
    def _detect_image_format(image_bytes: bytes) -> str:
        """
        Detect image format from magic bytes.

        Args:
            image_bytes: Image data

        Returns:
            Media type string (e.g., "image/jpeg")
        """
        if image_bytes[:2] == b'\xff\xd8':
            return "image/jpeg"
        elif image_bytes[:8] == b'\x89PNG\r\n\x1a\n':
            return "image/png"
        elif image_bytes[:4] == b'RIFF' and image_bytes[8:12] == b'WEBP':
            return "image/webp"
        elif image_bytes[:6] in (b'GIF87a', b'GIF89a'):
            return "image/gif"
        else:
            # Default to JPEG if unknown
            logger.warning("Unknown image format, defaulting to JPEG")
            return "image/jpeg"
