from typing import Dict, Any
from ..base_tool import BaseTool, ExecutionContext
from services import DatabaseService
import re


class JoinEventInviteTool(BaseTool):
    """Tool for joining an event via invite code (called from deep link)"""

    def __init__(self):
        super().__init__(
            name="join_event_invite",
            description="Join an event using an invite code from a deep link",
            input_schema={
                "type": "object",
                "properties": {
                    "invite_code": {
                        "type": "string",
                        "description": "Event invite code (format: evt_<16 chars>)",
                    },
                },
                "required": ["invite_code"],
            },
        )

    async def execute(
        self, tool_input: Dict[str, Any], ctx: ExecutionContext
    ) -> Dict[str, Any]:
        """Join an event using its invite code"""

        invite_code = tool_input.get("invite_code", "").strip()

        print(f"[JOIN_EVENT_INVITE] User {ctx.user.id} joining via code: {invite_code}")

        # Validate invite code format
        if not self._is_valid_format(invite_code):
            return {
                "success": False,
                "message": "Invalid invite code format.",
            }

        # Attempt to join the event
        result = DatabaseService.join_event_by_invite_code(
            ctx.db, ctx.user, invite_code
        )

        # Add more user-friendly messaging
        if result["success"]:
            if result.get("already_joined"):
                print(f"[JOIN_EVENT_INVITE] User already in event '{result['event_name']}'")
                return {
                    "success": True,
                    "message": (
                        f"You're already a member of '{result['event_name']}'!\n\n"
                        f"You can add memories to this event anytime."
                    ),
                    "event_id": result["event_id"],
                    "event_name": result["event_name"],
                }
            else:
                print(f"[JOIN_EVENT_INVITE] User successfully joined '{result['event_name']}'")
                return {
                    "success": True,
                    "message": (
                        f"Welcome! You've joined '{result['event_name']}'! 🎉\n\n"
                        f"You can now:\n"
                        f"- Add memories with photos and descriptions\n"
                        f"- View event memories\n"
                        f"- Generate invite links to share with others"
                    ),
                    "event_id": result["event_id"],
                    "event_name": result["event_name"],
                }

        print(f"[JOIN_EVENT_INVITE] Failed to join: {result.get('message')}")
        return result

    def _is_valid_format(self, code: str) -> bool:
        """Validate invite code format"""
        pattern = r"^evt_[a-z0-9]{16}$"
        return bool(re.match(pattern, code))
