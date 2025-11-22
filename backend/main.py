from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from database import get_db
from agent import AnthropicAgent
from agent.services import MessagingService
from agent.tools import get_registry, ExecutionContext
from services import DatabaseService, TelegramService, S3Service
from services.embedding import EmbeddingService
from services.image import ImageService
from services.search import SearchService
from schemas import TelegramUpdate
import os

app = FastAPI(title="Memories Bot API", version="1.0.0")

# Initialize services
agent = AnthropicAgent()
s3_service = S3Service()
telegram_service = TelegramService(os.getenv("TELEGRAM_BOT_TOKEN", ""))

# Get tool registry (tools are auto-registered on import)
tool_registry = get_registry()

# Initialize Messaging service (coordinates agent, telegram, and database)
messaging_service = MessagingService(
    agent=agent,
    telegram_service=telegram_service,
    database_service=DatabaseService,
    s3_service=s3_service
)


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "memories-bot"}


@app.post("/webhook")
async def telegram_webhook(update: TelegramUpdate, db: Session = Depends(get_db)):
    """
    Main webhook endpoint that receives raw Telegram updates and processes them.

    Receives a Telegram Update object, processes it with the AI agent via MessagingService,
    and returns a Telegram Bot API response.

    La lógica de procesamiento está ahora encapsulada en MessagingService.
    """
    return await messaging_service.process_response(update, db)
