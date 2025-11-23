import os
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
from services.speech import SpeechService
from schemas import TelegramUpdate
# Import models to ensure SQLAlchemy recognizes them
from models import User, Event, Memory, Message

app = FastAPI(title="Memories Bot API", version="1.0.0")

# Initialize services
agent = AnthropicAgent()
s3_service = S3Service()

# Initialize SpeechService if OpenAI API key is available
speech_service = None
try:
    speech_service = SpeechService()
    print("[MAIN] SpeechService initialized - voice messages will be transcribed")
except ValueError as e:
    print(f"[MAIN] SpeechService not initialized: {e}")
    print("[MAIN] Voice messages will not be transcribed")

telegram_service = TelegramService(
    bot_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
    speech_service=speech_service
)

image_service = ImageService(
    telegram_service=telegram_service,
    s3_service=s3_service
)

# Get tool registry (tools are auto-registered on import)
tool_registry = get_registry()

# Initialize Messaging service (coordinates agent, telegram, and database)
messaging_service = MessagingService(
    agent=agent,
    telegram_service=telegram_service,
    database_service=DatabaseService,
    s3_service=s3_service,
    image_service=image_service
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
