from typing import Dict, Any
from ..base_tool import BaseTool, ExecutionContext
from services import DatabaseService
import os


class GenerateInviteLinkTool(BaseTool):
    """Tool for generating shareable event invitation links"""

    def __init__(self):
        super().__init__(
            name="generate_invite_link",
            description="Generate a shareable Telegram invitation link for an event",
            input_schema={
                "type": "object",
                "properties": {
                    "event_id": {
                        "type": "integer",
                        "description": "ID of the event to generate invite link for",
                    },
                },
                "required": ["event_id"],
            },
        )

    async def execute(
        self, tool_input: Dict[str, Any], ctx: ExecutionContext
    ) -> Dict[str, Any]:
        """Generate an invite link for the specified event"""

        event_id = tool_input.get("event_id")

        print(f"[GENERATE_INVITE_LINK] Generating link for event #{event_id}")

        # Get event from database
        event = DatabaseService.get_event(ctx.db, event_id)

        if not event:
            return {"success": False, "message": f"Event #{event_id} not found."}

        # Check if user is member of event
        if event not in ctx.user.events:
            return {
                "success": False,
                "message": "You don't have permission to generate invite links for this event.",
            }

        # Generate the invite link
        bot_username = os.getenv("TELEGRAM_BOT_USERNAME", "memories_bot")
        invite_link = f"https://t.me/{bot_username}?start={event.invite_code}"

        print(f"[GENERATE_INVITE_LINK] Generated link: {invite_link}")

        return {
            "success": True,
            "message": f"Invite link for '{event.name}' created!",
            "invite_link": invite_link,
            "event_id": event_id,
            "event_name": event.name,
            "invite_code": event.invite_code,
        }
