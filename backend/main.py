import os
from dotenv import load_dotenv

# Load environment variables from the root .env file
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

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
# Import models to ensure SQLAlchemy recognizes them
from models import User, Event, Memory, Message

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


# ============================================================================
# API Endpoints for Frontend
# ============================================================================

from fastapi.middleware.cors import CORSMiddleware
from typing import List
from schemas import Memory as MemorySchema

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/memories", response_model=List[MemorySchema])
def get_memories(
    skip: int = 0, 
    limit: int = 50, 
    db: Session = Depends(get_db)
):
    """
    Get a list of memories (photos/videos) for the frontend feed.
    """
    memories = db.query(Memory).order_by(Memory.created_at.desc()).offset(skip).limit(limit).all()
    return memories
