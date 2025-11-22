from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from datetime import datetime
from database import get_db
from agent import AnthropicAgent
from services import DatabaseService, TelegramService, S3Service
from schemas import TelegramUpdate

app = FastAPI(title="Memories Bot API", version="1.0.0")

# Initialize services
agent = AnthropicAgent()
telegram_service = TelegramService()
s3_service = S3Service()


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
        photo = message.photo  # Array of PhotoSize objects

        # Prepare context for agent
        context = {
            "telegram_id": telegram_id,
            "username": username,
            "first_name": first_name,
            "last_name": last_name,
            "user_db_id": user.id,
            "has_photo": bool(photo)
        }

        # Process message with agent
        agent_response = await agent.process_message(text, context)

        action = agent_response.get("action")
        parameters = agent_response.get("parameters", {})
        response_text = agent_response.get("response_text", "")

        # Execute the action
        action_result = await execute_action(
            action=action,
            parameters=parameters,
            user=user,
            db=db,
            photo=photo,
            text=text
        )

        # Combine agent response with action result
        if action_result.get("success"):
            final_response = response_text or action_result.get("message", "Done!")
        else:
            final_response = action_result.get("message", "Sorry, something went wrong.")

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
        return {"status": "error", "message": str(e)}


async def execute_action(
    action: str,
    parameters: Dict[str, Any],
    user: Any,
    db: Session,
    photo: Optional[list] = None,
    text: Optional[str] = None
) -> Dict[str, Any]:
    """Execute the action determined by the agent"""

    try:
        if action == "create_event":
            name = parameters.get("name")
            description = parameters.get("description")
            event_date_str = parameters.get("event_date")

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
                "message": f"Event '{name}' created with ID {event.id}!"
            }

        elif action == "join_event":
            event_id = parameters.get("event_id")
            success = DatabaseService.join_event(db, user, event_id)

            if success:
                return {"success": True, "message": f"You joined event #{event_id}!"}
            else:
                return {"success": False, "message": "Event not found."}

        elif action == "add_memory":
            event_id = parameters.get("event_id")
            memory_text = parameters.get("text") or text

            # Handle image if present
            image_url = None
            if photo:
                # Get largest photo
                largest_photo = max(photo, key=lambda p: p.file_size or 0)
                file_id = largest_photo.file_id

                try:
                    # Download from Telegram
                    image_data = await telegram_service.download_file(file_id)

                    # Upload to S3 (or mock)
                    image_url = await s3_service.upload_image(image_data)
                except Exception as img_error:
                    print(f"Error handling image: {img_error}")
                    # Continue without image if download/upload fails

            # Save memory
            memory = DatabaseService.add_memory(
                db=db,
                user=user,
                event_id=event_id,
                text=memory_text,
                image_url=image_url
            )

            if memory:
                msg = f"Memory added to event #{event_id}!"
                if image_url:
                    msg += f"\nImage: {image_url}"
                return {"success": True, "message": msg}
            else:
                return {"success": False, "message": "Could not add memory. Make sure you're in this event."}

        elif action == "list_events":
            events = DatabaseService.list_user_events(db, user)

            if not events:
                return {"success": True, "message": "You're not in any events yet."}

            events_list = "\n".join([
                f"#{e.id}: {e.name}" + (f" - {e.description}" if e.description else "")
                for e in events
            ])
            return {"success": True, "message": f"Your events:\n{events_list}"}

        elif action == "list_memories":
            event_id = parameters.get("event_id")
            memories = DatabaseService.list_event_memories(db, event_id)

            if not memories:
                return {"success": True, "message": f"No memories in event #{event_id} yet."}

            memories_list = "\n\n".join([
                f"Memory #{m.id}:\n{m.text or '(photo only)'}\nBy: {m.user.first_name}"
                for m in memories
            ])
            return {"success": True, "message": f"Memories from event #{event_id}:\n\n{memories_list}"}

        elif action == "chat":
            # Just conversational, no action needed
            return {"success": True}

        else:
            return {"success": False, "message": "Unknown action."}

    except Exception as e:
        print(f"Error executing action {action}: {e}")
        return {"success": False, "message": f"Error: {str(e)}"}
