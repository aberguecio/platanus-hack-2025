import os
from dotenv import load_dotenv

# Load environment variables from the root .env file
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

from typing import List, Dict, Any
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
from models import User, Event, Memory, Message, LoginRequest
from database import engine, Base

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)

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


# ============================================================================
# Authentication Endpoints
# ============================================================================

from pydantic import BaseModel
from models.auth import LoginRequest
import uuid
from datetime import datetime, timedelta

class LoginPayload(BaseModel):
    phone_number: str

class VerifyPayload(BaseModel):
    token: str

class AuthResponse(BaseModel):
    token: str
    user: dict

@app.post("/auth/login")
async def login(payload: LoginPayload, db: Session = Depends(get_db)):
    """
    Initiate login flow.
    1. Find user by phone number.
    2. Generate magic link token.
    3. Send link via Telegram.
    """
    # Normalize phone number (basic)
    phone = payload.phone_number.strip()
    
    # Find user
    user = db.query(User).filter(User.phone_number == phone).first()
    if not user:
        # For security, don't reveal if user exists, but here we might want to be helpful
        # If user doesn't exist, we can't send telegram message easily unless we use phone number contact sharing
        # For this hackathon, assume user exists
        return {"message": "If your phone number is registered, you will receive a login link on Telegram."}

    # Generate token
    token = str(uuid.uuid4())
    expires_at = datetime.utcnow() + timedelta(minutes=15)
    
    login_request = LoginRequest(
        user_id=user.id,
        token=token,
        expires_at=expires_at
    )
    db.add(login_request)
    db.commit()
    
    # Send Telegram message
    # Link format: {FRONTEND_URL}/verify?token=...
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
    magic_link = f"{frontend_url}/verify?token={token}"
    print(f"MAGIC LINK: {magic_link}")
    
    try:
        await telegram_service.send_message(
            chat_id=int(user.telegram_id),
            text=f"🔐 Log in to Collective Diary:\n\n{magic_link}\n\nThis link expires in 15 minutes."
        )
    except Exception as e:
        print(f"Failed to send telegram message: {e}")
        return {"error": "Failed to send login link"}
        
    return {"message": "Login link sent to Telegram"}

@app.post("/auth/verify")
def verify(payload: VerifyPayload, db: Session = Depends(get_db)):
    """
    Verify magic link token.
    """
    login_req = db.query(LoginRequest).filter(
        LoginRequest.token == payload.token,
        LoginRequest.is_used == False,
        LoginRequest.expires_at > datetime.utcnow()
    ).first()
    
    if not login_req:
        return {"error": "Invalid or expired token"}
        
    # Mark as used
    login_req.is_used = True
    db.commit()
    
    user = login_req.user
    
    return {
        "token": "session_token_placeholder", # In a real app, issue a JWT here
        "user": {
            "id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "telegram_id": user.telegram_id
        }
    }
@app.post("/webhook/batch")
async def webhook_batch(
    payload: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """
    Batch webhook endpoint que recibe múltiples updates de Telegram agrupados.

    Este endpoint es llamado por el ARQ worker después de que expira la ventana
    de agrupación (12.5 segundos). Procesa todos los mensajes como un solo batch,
    lo cual es especialmente útil para múltiples fotos.

    Args:
        payload: Dict con 'updates' (lista de Telegram updates) y 'user_id'
        db: Database session

    Returns:
        Dict con método y respuesta de Telegram Bot API
    """
    updates = payload.get("updates", [])
    user_id = payload.get("user_id")

    if not updates:
        return {"error": "No updates provided"}

    print(f"[BATCH] Processing {len(updates)} messages for user {user_id}")

    # Procesar batch usando MessagingService
    response = await messaging_service.process_message_batch(
        updates=updates,
        db=db
    )

    print(f"[BATCH] Batch processed successfully")
    return response
