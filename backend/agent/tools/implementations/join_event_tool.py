from typing import Dict, Any
from ..base_tool import BaseTool, ExecutionContext
from services import DatabaseService


class JoinEventTool(BaseTool):
    """Tool for joining an existing event"""

    def __init__(self):
        super().__init__(
            name="join_event",
            description="Add the user to an existing event",
            input_schema={
                "type": "object",
                "properties": {
                    "event_id": {
                        "type": "integer",
                        "description": "ID of the event to join",
                    },
                },
                "required": ["event_id"],
            },
        )

    async def execute(
        self, tool_input: Dict[str, Any], ctx: ExecutionContext
    ) -> Dict[str, Any]:
        """Join an existing event"""

        event_id = tool_input.get("event_id")

        success = DatabaseService.join_event(ctx.db, ctx.user, event_id)

        if success:
            return {"success": True, "message": f"Joined event #{event_id}!"}
        else:
            return {"success": False, "message": "Event not found."}

