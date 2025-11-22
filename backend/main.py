from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from datetime import datetime
from database import get_db
from agent import AnthropicAgent
from services import DatabaseService, TelegramService, S3Service
from schemas import TelegramUpdate
from models import User

app = FastAPI(title="Memories Bot API", version="1.0.0")

# Initialize services
agent = AnthropicAgent()
s3_service = S3Service()


# Tool executor function that the agent will call
async def tool_executor(tool_name: str, tool_input: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a tool and return the result"""
    from database import SessionLocal

    db = SessionLocal()
    try:
        # Get user from context
        user_id = context.get("user_db_id")
        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            return {"success": False, "message": "User not found"}

        # Execute the tool based on name
        if tool_name == "create_event":
            name = tool_input.get("name")
            description = tool_input.get("description")
            event_date_str = tool_input.get("event_date")

            event_date = None
            if event_date_str:
                try:
                    event_date = datetime.fromisoformat(event_date_str)
                except:
                    pass

            event = DatabaseService.create_event(
                db=db,
                name=name,
                description=description,
                event_date=event_date
            )

            # Automatically add creator to event
            DatabaseService.join_event(db, user, event.id)

            return {
                "success": True,
                "message": f"Event '{name}' created with ID #{event.id}!",
                "event_id": event.id
            }

        elif tool_name == "join_event":
            event_id = tool_input.get("event_id")
            success = DatabaseService.join_event(db, user, event_id)

            if success:
                return {"success": True, "message": f"Joined event #{event_id}!"}
            else:
                return {"success": False, "message": "Event not found."}

        elif tool_name == "add_memory":
            event_id = tool_input.get("event_id")
            memory_text = tool_input.get("text")

            # Handle image from context if available
            photo_file_id = context.get("photo_file_id")
            image_url = None

            print(f"[TOOL] add_memory - event_id: {event_id}")
            print(f"[TOOL] add_memory - memory_text: {memory_text}")
            print(f"[TOOL] add_memory - context.has_photo: {context.get('has_photo')}")
            print(f"[TOOL] add_memory - photo_file_id from context: {photo_file_id}")

            # If there's a photo, download from Telegram and upload to S3
            if photo_file_id:
                import os
                bot_token = os.getenv("TELEGRAM_BOT_TOKEN")

                if not bot_token:
                    print("[TOOL] ERROR: TELEGRAM_BOT_TOKEN not found in environment")
                    image_url = photo_file_id  # Fallback to file_id
                else:
                    try:
                        print(f"[TOOL] Downloading photo from Telegram...")
                        telegram_service = TelegramService(bot_token)
                        image_data = await telegram_service.download_file(photo_file_id)
                        print(f"[TOOL] Photo downloaded, size: {len(image_data)} bytes")

                        # Upload to S3
                        print(f"[TOOL] Uploading to S3...")
                        image_url = await s3_service.upload_image(image_data, f"memory_{event_id}_{photo_file_id[:20]}.jpg")
                        print(f"[TOOL] Image uploaded to S3: {image_url}")
                    except Exception as img_error:
                        print(f"[TOOL] Error handling image: {img_error}")
                        import traceback
                        traceback.print_exc()
                        # Fallback to file_id if download/upload fails
                        image_url = photo_file_id

            memory = DatabaseService.add_memory(
                db=db,
                user=user,
                event_id=event_id,
                text=memory_text,
                image_url=image_url
            )

            if memory:
                result_msg = f"Memory added to event #{event_id}!"
                if image_url:
                    if image_url.startswith('http'):
                        result_msg += f" (photo uploaded to S3)"
                    else:
                        result_msg += f" (photo saved as Telegram file_id)"
                return {"success": True, "message": result_msg}
            else:
                return {"success": False, "message": "Could not add memory. Make sure you're in this event."}

        elif tool_name == "list_events":
            events = DatabaseService.list_user_events(db, user)

            if not events:
                return {"success": True, "message": "No events yet.", "events": []}

            events_list = [
                {"id": e.id, "name": e.name, "description": e.description}
                for e in events
            ]
            return {
                "success": True,
                "message": "Events retrieved",
                "events": events_list,
                "count": len(events_list)
            }

        elif tool_name == "list_memories":
            event_id = tool_input.get("event_id")
            memories = DatabaseService.list_event_memories(db, event_id)

            if not memories:
                return {"success": True, "message": f"No memories in event #{event_id} yet.", "memories": []}

            memories_list = []
            for m in memories:
                # Generate presigned URL if image is stored in S3
                image_url = m.image_url
                print(f"[TOOL] list_memories - original image_url: {image_url}")

                if image_url and image_url.startswith('s3://'):
                    presigned_url = s3_service.generate_presigned_url(image_url, expiration=3600)
                    print(f"[TOOL] list_memories - presigned URL generated: {presigned_url[:100]}...")
                    image_url = presigned_url

                memories_list.append({
                    "id": m.id,
                    "text": m.text or "(photo only)",
                    "user": m.user.first_name,
                    "image_url": image_url,
                    "has_image": bool(m.image_url),
                    "created_at": m.created_at.isoformat() if m.created_at else None
                })

            return {
                "success": True,
                "message": "Memories retrieved",
                "memories": memories_list,
                "count": len(memories_list)
            }

        elif tool_name == "get_faq":
            topic = tool_input.get("topic", "general")

            faq_content = {
                "upload_image": {
                    "title": "How to upload an image/photo",
                    "steps": [
                        "1. First, create an event or make sure you're part of one (use 'list my events' to check)",
                        "2. Send a photo directly to the bot (using Telegram's photo upload)",
                        "3. You can optionally add a caption to the photo",
                        "4. The bot will ask which event to add it to, or you can say 'add this to event #X'",
                        "5. The photo will be stored as a memory in that event!"
                    ],
                    "example": "Just send a photo and say 'add this to event #1' or 'save this memory to hackaton event'"
                },
                "invite_user": {
                    "title": "How to invite people to an event",
                    "steps": [
                        "Currently, each user manages their own events independently.",
                        "To share an event:",
                        "1. Tell your friend the event ID (e.g., #1)",
                        "2. They can say 'join event #1' to join",
                        "3. Once joined, they can add their own memories to the event",
                        "4. Both of you will see all memories in the shared event!"
                    ],
                    "note": "Event IDs are numbers like #1, #2, #3, etc."
                },
                "create_event": {
                    "title": "How to create an event",
                    "steps": [
                        "Just tell me what event you want to create!",
                        "Examples:",
                        "- 'Create event Birthday Party'",
                        "- 'Create a new event named Summer Trip'",
                        "- 'New event: Graduation 2025'",
                        "You can optionally add a date:",
                        "- 'Create event Christmas on 2025-12-25'",
                        "You'll automatically be added to events you create!"
                    ]
                },
                "add_memory": {
                    "title": "How to add a memory",
                    "steps": [
                        "You can add both text and photo memories:",
                        "Text memory:",
                        "- 'Add memory to event #1: Had a great time!'",
                        "- 'Save to hackaton: Met amazing people'",
                        "Photo memory:",
                        "- Send a photo and say 'add to event #1'",
                        "- Or send photo with caption: 'for event #2'",
                        "Combined:",
                        "- Send a photo with a descriptive caption"
                    ]
                },
                "general": {
                    "title": "General Help - What I can do",
                    "capabilities": [
                        "📅 Create events: 'Create event [name]'",
                        "👥 Join events: 'Join event #1'",
                        "💭 Add memories: 'Add memory to event #1: [text]'",
                        "📸 Upload photos: Send a photo directly",
                        "📋 List your events: 'Show my events' or 'List events'",
                        "🔍 View memories: 'Show memories from event #1'",
                    ],
                    "tips": [
                        "Events have IDs like #1, #2, #3",
                        "You can have multiple events",
                        "Share event IDs with friends so they can join",
                        "Photos and text are both supported"
                    ]
                }
            }

            faq = faq_content.get(topic, faq_content["general"])
            return {
                "success": True,
                "faq": faq,
                "topic": topic
            }

        else:
            return {"success": False, "message": f"Unknown tool: {tool_name}"}

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

    Receives a Telegram Update object, processes it with the AI agent,
    and returns a Telegram Bot API response.
    """
    try:
        # Extract message data
        message = update.message
        if not message:
            return {"status": "ignored", "reason": "no_message"}

        # Extract user info
        from_user = message.from_
        if not from_user:
            return {"status": "ignored", "reason": "no_user"}

        telegram_id = str(from_user.id)
        username = from_user.username
        first_name = from_user.first_name
        last_name = from_user.last_name
        chat_id = message.chat.id

        # Get or create user
        user = DatabaseService.get_or_create_user(
            db=db,
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name
        )

        # Extract message content
        text = message.text or ""
        caption = message.caption or ""  # Photo captions come in a different field
        photo = message.photo  # Array of PhotoSize objects

        # DEBUG LOGS
        print(f"\n[WEBHOOK] Received update:")
        print(f"[WEBHOOK] - message.text: '{text}'")
        print(f"[WEBHOOK] - message.caption: '{caption}'")
        print(f"[WEBHOOK] - message.photo: {bool(photo)} (count: {len(photo) if photo else 0})")

        # Handle photo if present
        photo_file_id = None
        if photo:
            largest_photo = max(photo, key=lambda p: p.file_size or 0)
            photo_file_id = largest_photo.file_id
            print(f"[WEBHOOK] - photo_file_id: {photo_file_id}")

        # Use caption if photo has one, otherwise use text
        if photo and caption.strip():
            text = caption
            print(f"[WEBHOOK] Using caption as text: '{text}'")
        elif photo and not text.strip():
            # If user sent only a photo without text/caption, create a default message
            text = "I sent you a photo. Please help me save it as a memory."
            print(f"[WEBHOOK] Photo without caption, using default message")

        print(f"[WEBHOOK] Final text to process: '{text}'")
        print(f"[WEBHOOK] Has photo: {bool(photo)}")
        print()

        # Prepare context for agent
        context = {
            "telegram_id": telegram_id,
            "username": username,
            "first_name": first_name,
            "last_name": last_name,
            "user_db_id": user.id,
            "has_photo": bool(photo),
            "photo_file_id": photo_file_id
        }

        # Process message with agent - it now handles tool execution internally
        final_response = await agent.process_message(text, context)

        # Return response for the bot to send
        # Using Telegram Bot API response format
        return {
            "method": "sendMessage",
            "chat_id": chat_id,
            "text": final_response,
            "parse_mode": "Markdown"
        }

    except Exception as e:
        print(f"Error processing webhook: {e}")
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": str(e)}
