from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
from models import (
    User, Event, Memory, user_events,
    Channel, AIMemoryAssistant, Conversation, Message,
    MediaTypeEnum, ChannelTypeEnum, ConversationStatusEnum, MessageDirectionEnum
)

logger = logging.getLogger(__name__)

class DatabaseService:
    """Service for database operations"""

    @staticmethod
    def get_or_create_user(
        db: Session,
        telegram_id: str,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None
    ) -> User:
        """Get existing user or create new one"""
        user = db.query(User).filter(User.telegram_id == telegram_id).first()

        if not user:
            user = User(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                last_name=last_name
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            # Update user info if changed
            if username and user.username != username:
                user.username = username
            if first_name and user.first_name != first_name:
                user.first_name = first_name
            if last_name and user.last_name != last_name:
                user.last_name = last_name
            db.commit()

        return user

    @staticmethod
    def create_event(
        db: Session,
        name: str,
        description: Optional[str] = None,
        event_date: Optional[datetime] = None
    ) -> Event:
        """Create a new event"""
        event = Event(
            name=name,
            description=description,
            event_date=event_date
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        return event

    @staticmethod
    def join_event(db: Session, user: User, event_id: int) -> bool:
        """Add user to an event"""
        event = db.query(Event).filter(Event.id == event_id).first()
        if not event:
            return False

        if event not in user.events:
            user.events.append(event)
            db.commit()

        return True

    @staticmethod
    def add_memory(
        db: Session,
        user: User,
        event_id: int,
        text: Optional[str] = None,
        s3_url: Optional[str] = None,
        image_description: Optional[str] = None,
        media_type: Optional[MediaTypeEnum] = None,
        memory_metadata: Optional[Dict[str, Any]] = None,
        message_id: Optional[int] = None
    ) -> Optional[Memory]:
        """Add a memory to an event"""
        event = db.query(Event).filter(Event.id == event_id).first()
        if not event or event not in user.events:
            return None

        memory = Memory(
            event_id=event_id,
            user_id=user.id,
            text=text,
            s3_url=s3_url,
            image_description=image_description,
            media_type=media_type,
            memory_metadata=memory_metadata,
            message_id=message_id
        )
        db.add(memory)
        db.commit()
        db.refresh(memory)
        return memory

    @staticmethod
    def list_user_events(db: Session, user: User) -> List[Event]:
        """List all events for a user"""
        return user.events

    @staticmethod
    def list_event_memories(db: Session, event_id: int) -> List[Memory]:
        """List all memories for an event"""
        return db.query(Memory).filter(Memory.event_id == event_id).all()

    @staticmethod
    def get_event(db: Session, event_id: int) -> Optional[Event]:
        """Get an event by ID"""
        return db.query(Event).filter(Event.id == event_id).first()

    # ========================================================================
    # Channel Operations
    # ========================================================================

    @staticmethod
    def get_or_create_channel(
        db: Session,
        name: str,
        type: ChannelTypeEnum,
        identifier: str
    ) -> Channel:
        """Get existing channel or create new one"""
        # Use enum value for filtering (PostgreSQL native enums need the value string)
        type_value = type.value if hasattr(type, 'value') else str(type)
        channel = db.query(Channel).filter(
            Channel.type == type_value,
            Channel.identifier == identifier
        ).first()

        if not channel:
            # When creating, use the enum member itself (SQLAlchemy will handle conversion)
            channel = Channel(name=name, type=type, identifier=identifier)
            db.add(channel)
            db.commit()
            db.refresh(channel)

        return channel

    @staticmethod
    def get_channel(db: Session, channel_id: int) -> Optional[Channel]:
        """Get a channel by ID"""
        return db.query(Channel).filter(Channel.id == channel_id).first()

    # ========================================================================
    # AIMemoryAssistant Operations
    # ========================================================================

    @staticmethod
    def create_assistant(
        db: Session,
        instructions: str,
        personality: Optional[str] = None
    ) -> AIMemoryAssistant:
        """Create a new AI assistant"""
        assistant = AIMemoryAssistant(
            instructions=instructions,
            personality=personality
        )
        db.add(assistant)
        db.commit()
        db.refresh(assistant)
        return assistant

    @staticmethod
    def get_assistant(db: Session, assistant_id: int) -> Optional[AIMemoryAssistant]:
        """Get an assistant by ID"""
        return db.query(AIMemoryAssistant).filter(AIMemoryAssistant.id == assistant_id).first()

    @staticmethod
    def list_assistants(db: Session) -> List[AIMemoryAssistant]:
        """List all assistants"""
        return db.query(AIMemoryAssistant).all()

    # ========================================================================
    # Conversation Operations
    # ========================================================================

    @staticmethod
    def create_conversation(
        db: Session,
        user_id: int,
        assistant_id: int,
        channel_id: int,
        title: Optional[str] = None,
        status: ConversationStatusEnum = ConversationStatusEnum.ACTIVE
    ) -> Conversation:
        """Create a new conversation"""
        conversation = Conversation(
            user_id=user_id,
            assistant_id=assistant_id,
            channel_id=channel_id,
            title=title,
            status=status
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        return conversation

    @staticmethod
    def get_conversation(db: Session, conversation_id: int) -> Optional[Conversation]:
        """Get a conversation by ID"""
        return db.query(Conversation).filter(Conversation.id == conversation_id).first()

    @staticmethod
    def list_user_conversations(
        db: Session,
        user_id: int,
        status: Optional[ConversationStatusEnum] = None
    ) -> List[Conversation]:
        """List conversations for a user, optionally filtered by status"""
        query = db.query(Conversation).filter(Conversation.user_id == user_id)
        if status:
            query = query.filter(Conversation.status == status)
        return query.order_by(Conversation.updated_at.desc()).all()

    @staticmethod
    def update_conversation_status(
        db: Session,
        conversation_id: int,
        status: ConversationStatusEnum
    ) -> Optional[Conversation]:
        """Update conversation status"""
        conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if conversation:
            conversation.status = status
            db.commit()
            db.refresh(conversation)
        return conversation

    @staticmethod
    def get_or_create_conversation(
        db: Session,
        user_id: int,
        channel_identifier: str = "telegram",
        assistant_instructions: str = "You are a helpful assistant for a memories storage bot."
    ) -> Conversation:
        """Get existing active conversation or create new one for a user"""
        # Get or create Telegram channel
        channel = DatabaseService.get_or_create_channel(
            db=db,
            name="Telegram",
            type=ChannelTypeEnum.TELEGRAM,
            identifier=channel_identifier
        )
        
        # Get or create default assistant
        assistant = db.query(AIMemoryAssistant).first()
        if not assistant:
            assistant = DatabaseService.create_assistant(
                db=db,
                instructions=assistant_instructions
            )
        
        # Get active conversation for this user
        conversation = db.query(Conversation).filter(
            Conversation.user_id == user_id,
            Conversation.channel_id == channel.id,
            Conversation.status == ConversationStatusEnum.ACTIVE
        ).first()
        
        if not conversation:
            conversation = DatabaseService.create_conversation(
                db=db,
                user_id=user_id,
                assistant_id=assistant.id,
                channel_id=channel.id
            )
        
        return conversation

    # ========================================================================
    # Message Operations
    # ========================================================================

    @staticmethod
    def add_message(
        db: Session,
        conversation_id: int,
        direction: MessageDirectionEnum,
        content: str
    ) -> Message:
        """Add a message to a conversation"""
        message = Message(
            conversation_id=conversation_id,
            direction=direction,
            content=content
        )
        db.add(message)
        db.commit()
        db.refresh(message)

        # Update conversation's updated_at timestamp
        conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if conversation:
            conversation.updated_at = datetime.utcnow()
            db.commit()

        return message

    @staticmethod
    async def save_message(
        db: Session,
        conversation_id: int,
        direction: MessageDirectionEnum,
        content: str,
        photo_file_id: Optional[str] = None,
        telegram_service: Optional[Any] = None,
        image_service: Optional[Any] = None,
        s3_service: Optional[Any] = None
    ) -> Message:
        """
        Save a message to the database with embedding generation.
        
        Args:
            db: Database session
            conversation_id: ID of the conversation
            direction: Direction of the message (USER or ASSISTANT)
            content: Content of the message
            photo_file_id: Optional Telegram file_id for photo
            telegram_service: Optional TelegramService for downloading photos
            image_service: Optional ImageService for processing images
            s3_service: Optional S3Service for uploading photos
            
        Returns:
            Created Message object
        """
        embedding = None
        embedding_text = content
        photo_s3_url = None
        image_description = None

        # Process image if present
        if photo_file_id and image_service:
            try:
                logger.info(f"[DATABASE_SERVICE] Processing photo for message: {photo_file_id}")
                # Generate image description and upload to S3
                description, s3_url = await image_service.process_telegram_photo(
                    file_id=photo_file_id,
                    store_in_s3=True
                )
                photo_s3_url = s3_url
                image_description = description  # Store description for context
                embedding_text = description
                logger.info(f"[DATABASE_SERVICE] Photo uploaded to S3: {s3_url}")
                logger.info(f"[DATABASE_SERVICE] Generated image description ({len(description)} chars)")
            except Exception as e:
                logger.error(f"[DATABASE_SERVICE] Error processing image: {e}")
                # Continue with text content as fallback
                embedding_text = content
        
        # Generate embedding
        if embedding_text and embedding_text.strip():
            try:
                from services.embedding import EmbeddingService
                logger.info(f"[DATABASE_SERVICE] Generating embedding for message...")
                embedding = EmbeddingService.embed_text(
                    embedding_text,
                    input_type="document"
                )
                logger.info(f"[DATABASE_SERVICE] Embedding generated successfully ({len(embedding)} dimensions)")
            except Exception as e:
                logger.error(f"[DATABASE_SERVICE] Error generating embedding: {e}")
                # Continue without embedding - don't block message save
        
        # Create message with embedding, photo URL, and image description
        message = Message(
            conversation_id=conversation_id,
            direction=direction,
            content=content,
            photo_s3_url=photo_s3_url,
            image_description=image_description,
            embedding=embedding
        )
        db.add(message)
        db.commit()
        db.refresh(message)

        # Update conversation's updated_at timestamp
        conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if conversation:
            conversation.updated_at = datetime.utcnow()
            db.commit()

        return message

    @staticmethod
    def list_conversation_messages(
        db: Session,
        conversation_id: int,
        limit: Optional[int] = None
    ) -> List[Message]:
        """List messages in a conversation"""
        query = db.query(Message).filter(Message.conversation_id == conversation_id).order_by(Message.created_at)
        if limit:
            query = query.limit(limit)
        return query.all()

    @staticmethod
    def get_message(db: Session, message_id: int) -> Optional[Message]:
        """Get a message by ID"""
        return db.query(Message).filter(Message.id == message_id).first()

    @staticmethod
    def get_recent_messages(
        db: Session,
        conversation_id: int,
        limit: int = 10
    ) -> List[Message]:
        """
        Get the most recent messages for a conversation.
        
        Args:
            db: Database session
            conversation_id: ID of the conversation
            limit: Maximum number of messages to retrieve (default: 10)
            
        Returns:
            List of Message objects ordered by created_at descending (most recent first)
        """
        return db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(
            Message.created_at.desc()
        ).limit(limit).all()

    @staticmethod
    def get_event_by_invite_code(db: Session, invite_code: str) -> Optional[Event]:
        """Get an event by its invite code"""
        return db.query(Event).filter(Event.invite_code == invite_code).first()

    @staticmethod
    def join_event_by_invite_code(db: Session, user: User, invite_code: str) -> Dict[str, Any]:
        """
        Join an event using an invite code.

        Returns:
            Dict with:
            - success: bool
            - message: str
            - event_id: int (if successful)
            - event_name: str (if successful)
        """
        event = DatabaseService.get_event_by_invite_code(db, invite_code)

        if not event:
            return {"success": False, "message": "Invalid invite code. Event not found."}

        if event in user.events:
            return {
                "success": True,
                "message": f"You're already in event '{event.name}'!",
                "event_id": event.id,
                "event_name": event.name,
                "already_joined": True
            }

        user.events.append(event)
        db.commit()

        return {
            "success": True,
            "message": f"Successfully joined '{event.name}'!",
            "event_id": event.id,
            "event_name": event.name
        }
