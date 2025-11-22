from typing import Dict, Any
from ..base_tool import BaseTool, ExecutionContext
from services import DatabaseService


class ListEventsTool(BaseTool):
    """Tool for listing all user's events"""

    def __init__(self):
        super().__init__(
            name="list_events",
            description="List all events the user is part of",
            input_schema={
                "type": "object",
                "properties": {},
            },
        )

    async def execute(
        self, tool_input: Dict[str, Any], ctx: ExecutionContext
    ) -> Dict[str, Any]:
        """List all events for the current user"""

        events = DatabaseService.list_user_events(ctx.db, ctx.user)

        if not events:
            return {"success": True, "message": "No events yet.", "events": []}

        events_list = [
            {"id": e.id, "name": e.name, "description": e.description} for e in events
        ]

        return {
            "success": True,
            "message": "Events retrieved",
            "events": events_list,
            "count": len(events_list),
        }

