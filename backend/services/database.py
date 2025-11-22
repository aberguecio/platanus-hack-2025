from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from models import User, Event, Memory, Message, user_events

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
        image_url: Optional[str] = None
    ) -> Optional[Memory]:
        """Add a memory to an event"""
        event = db.query(Event).filter(Event.id == event_id).first()
        if not event or event not in user.events:
            return None

        memory = Memory(
            event_id=event_id,
            user_id=user.id,
            text=text,
            image_url=image_url
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

    @staticmethod
    def save_message(
        db: Session,
        user_id: int,
        role: str,
        content: str
    ) -> Message:
        """
        Save a message to the database.
        
        Args:
            db: Database session
            user_id: ID of the user
            role: Role of the message sender ("user" or "assistant")
            content: Content of the message
            
        Returns:
            Created Message object
        """
        message = Message(
            user_id=user_id,
            role=role,
            content=content
        )
        db.add(message)
        db.commit()
        db.refresh(message)
        return message

    @staticmethod
    def get_recent_messages(
        db: Session,
        user_id: int,
        limit: int = 10
    ) -> List[Message]:
        """
        Get the most recent messages for a user.
        
        Args:
            db: Database session
            user_id: ID of the user
            limit: Maximum number of messages to retrieve (default: 10)
            
        Returns:
            List of Message objects ordered by created_at descending (most recent first)
        """
        return db.query(Message).filter(
            Message.user_id == user_id
        ).order_by(
            Message.created_at.desc()
        ).limit(limit).all()
