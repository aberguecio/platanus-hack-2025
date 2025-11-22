import os
import httpx
from typing import Optional

class TelegramService:
    """Service for sending messages to Telegram"""

    def __init__(self, bot_token: Optional[str] = None):
        self.bot_token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN")
        if not self.bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")

        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"

    async def send_message(
        self,
        chat_id: int,
        text: str,
        parse_mode: str = "Markdown"
    ) -> dict:
        """Send a text message to a chat"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": text,
                    "parse_mode": parse_mode
                }
            )
            return response.json()

    async def download_file(self, file_id: str) -> bytes:
        """Download a file from Telegram"""
        async with httpx.AsyncClient() as client:
            # Get file path
            response = await client.get(
                f"{self.base_url}/getFile",
                params={"file_id": file_id}
            )
            file_path = response.json()["result"]["file_path"]

            # Download file
            file_response = await client.get(
                f"https://api.telegram.org/file/bot{self.bot_token}/{file_path}"
            )
            return file_response.content
