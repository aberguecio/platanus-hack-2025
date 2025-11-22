

class CreateEventTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="create_event",
            description="Create a new event",
            input_schema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Name of the event"},
                    "description": {"type": "string", "description": "Description of the event"},
                    "event_date": {"type": "string", "description": "Date of the event (ISO format)"},
                }
            }
        )
      def execute(self, input: dict) -> dict:
        pass