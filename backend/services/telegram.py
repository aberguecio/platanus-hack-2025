import httpx
from typing import Optional

class TelegramService:
    """Service for downloading files from Telegram"""

    def __init__(self, bot_token: str):
        self.bot_token = bot_token
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"

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
