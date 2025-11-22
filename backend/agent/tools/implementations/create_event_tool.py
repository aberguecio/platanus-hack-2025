from typing import Dict, Any
from datetime import datetime
from ..base_tool import BaseTool, ExecutionContext
from services import DatabaseService


class CreateEventTool(BaseTool):
    """Tool for creating new events"""

    def __init__(self):
        super().__init__(
            name="create_event",
            description="Create a new event for storing memories",
            input_schema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Name of the event",
                    },
                    "description": {
                        "type": "string",
                        "description": "Description of the event",
                    },
                    "event_date": {
                        "type": "string",
                        "description": "Date of the event (ISO format)",
                    },
                },
                "required": ["name"],
            },
        )

    async def execute(
        self, tool_input: Dict[str, Any], ctx: ExecutionContext
    ) -> Dict[str, Any]:
        """Create a new event and automatically add the creator to it"""

        # Extract parameters
        name = tool_input.get("name")
        description = tool_input.get("description")
        event_date_str = tool_input.get("event_date")

        # Parse event date if provided
        event_date = None
        if event_date_str:
            try:
                event_date = datetime.fromisoformat(event_date_str)
            except ValueError:
                # Invalid date format, continue without date
                pass

        # Create the event
        event = DatabaseService.create_event(
            db=ctx.db, name=name, description=description, event_date=event_date
        )

        # Automatically add creator to event
        DatabaseService.join_event(ctx.db, ctx.user, event.id)

        return {
            "success": True,
            "message": f"Event '{name}' created with ID #{event.id}!",
            "event_id": event.id,
        }

