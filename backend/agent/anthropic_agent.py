import os
import json
from typing import Dict, Any, Optional
from anthropic import Anthropic
from .base import LLMAgent

class AnthropicAgent(LLMAgent):
    """
    Anthropic Claude implementation of the LLM agent.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is required")

        self.client = Anthropic(api_key=self.api_key)
        # Using Claude 3 Haiku - fastest and cheapest model
        self.model = "claude-3-haiku-20240307"

    async def process_message(
        self,
        user_message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process message using Claude with tool calling for structured actions.
        """
        context = context or {}

        # Define available tools/actions
        tools = [
            {
                "name": "create_event",
                "description": "Create a new event for storing memories",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Name of the event"},
                        "description": {"type": "string", "description": "Description of the event"},
                        "event_date": {"type": "string", "description": "Date of the event (ISO format)"},
                    },
                    "required": ["name"]
                }
            },
            {
                "name": "join_event",
                "description": "Add the user to an existing event",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "event_id": {"type": "integer", "description": "ID of the event to join"},
                    },
                    "required": ["event_id"]
                }
            },
            {
                "name": "add_memory",
                "description": "Add a memory (text and/or image) to an event",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "event_id": {"type": "integer", "description": "ID of the event"},
                        "text": {"type": "string", "description": "Text content of the memory"},
                        "has_image": {"type": "boolean", "description": "Whether this memory includes an image"},
                    },
                    "required": ["event_id"]
                }
            },
            {
                "name": "list_events",
                "description": "List all events the user is part of",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                }
            },
            {
                "name": "list_memories",
                "description": "List memories from a specific event",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "event_id": {"type": "integer", "description": "ID of the event"},
                    },
                    "required": ["event_id"]
                }
            }
        ]

        # Build system prompt with context
        system_prompt = f"""You are a helpful assistant for a memories storage bot on Telegram.
Users can create events and store memories (photos and text) in them.

Current user context:
- Telegram ID: {context.get('telegram_id', 'unknown')}
- Username: {context.get('username', 'unknown')}
- First name: {context.get('first_name', 'unknown')}

Your job is to:
1. Understand what the user wants to do
2. Call the appropriate tool with the right parameters
3. Provide a friendly response

Available actions:
- create_event: Create a new event
- join_event: Join an existing event
- add_memory: Add a memory to an event
- list_events: Show user's events
- list_memories: Show memories from an event
"""

        # Call Claude API with tools
        response = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            system=system_prompt,
            tools=tools,
            messages=[
                {
                    "role": "user",
                    "content": user_message
                }
            ]
        )

        # Parse response
        result = {
            "action": None,
            "parameters": {},
            "response_text": ""
        }

        # Extract tool use and text
        for block in response.content:
            if block.type == "tool_use":
                result["action"] = block.name
                result["parameters"] = block.input
            elif block.type == "text":
                result["response_text"] = block.text

        # If no tool was used, generate a conversational response
        if not result["action"]:
            result["action"] = "chat"
            result["response_text"] = result["response_text"] or "I'm not sure what you want to do. Can you please clarify?"

        return result

    async def generate_response(self, prompt: str) -> str:
        """
        Generate a simple text response.
        """
        response = self.client.messages.create(
            model=self.model,
            max_tokens=512,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        return response.content[0].text
