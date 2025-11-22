from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
import os
from database import get_db
from agent import AnthropicAgent
from agent.services import MessagingService
from agent.tools import get_registry, ExecutionContext
from services import DatabaseService, TelegramService, S3Service
from services.embedding import EmbeddingService
from services.image import ImageService
from services.search import SearchService
from schemas import TelegramUpdate
from models import User

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
    database_service=DatabaseService
)

# Initialize Telegram service for downloading files
telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
if telegram_bot_token:
    telegram_service = TelegramService(telegram_bot_token)
    image_service = ImageService(telegram_service=telegram_service, s3_service=s3_service)
else:
    telegram_service = None
    image_service = None


# Tool executor function that the agent will call
async def tool_executor(
    tool_name: str, tool_input: Dict[str, Any], context: Dict[str, Any]
) -> Dict[str, Any]:
    """Execute a tool using the tool registry"""
    from database import SessionLocal

    db = SessionLocal()
    try:
        # Get user from context
        user_id = context.get("user_db_id")
        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            return {"success": False, "message": "User not found"}

        # Create execution context with all dependencies
        ctx = ExecutionContext(
            db=db,
            user=user,
            s3_service=s3_service,
            telegram_service=telegram_service,
            metadata=context,
        )

        # Execute tool via registry
        return await tool_registry.execute(tool_name, tool_input, ctx)

    finally:
        db.close()


# Set the tool executor on the agent
agent.set_tool_executor(tool_executor)


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
