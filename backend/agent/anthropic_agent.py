import os
import json
from typing import Dict, Any, Optional, Callable
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
        self.model = "claude-haiku-4-5-20251001" #"claude-3-haiku-20240307"

        # Store tool executor function (will be set externally)
        self.tool_executor: Optional[Callable] = None

    def set_tool_executor(self, executor: Callable):
        """Set the function that will execute tools"""
        self.tool_executor = executor

    async def process_message(
        self,
        user_message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Process message using Claude with tool calling for structured actions.
        Returns the final text response after executing all necessary tools.
        """
        context = context or {}

        # Handle empty messages
        if not user_message or not user_message.strip():
            return "Please send me a message!"

        print(f"\n[AGENT] Processing message: {user_message}")

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
            },
            {
                "name": "get_faq",
                "description": "Get help and instructions about how to use the bot features",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "topic": {
                            "type": "string",
                            "description": "The help topic: 'upload_image', 'invite_user', 'create_event', 'add_memory', 'general'",
                            "enum": ["upload_image", "invite_user", "create_event", "add_memory", "general"]
                        }
                    },
                    "required": ["topic"]
                }
            # },
            # {
            #     "name": "search_memories",
            #     "description": "Search memories by semantic similarity across text and image descriptions. Use this when user wants to find specific memories by content, topic, or theme.",
            #     "input_schema": {
            #         "type": "object",
            #         "properties": {
            #             "query": {
            #                 "type": "string",
            #                 "description": "Search query describing what to look for (e.g., 'beach photos', 'team dinner', 'presentations')"
            #             },
            #             "event_id": {
            #                 "type": "integer",
            #                 "description": "Optional: limit search to specific event. If not provided, searches across all user's events"
            #             },
            #             "top_k": {
            #                 "type": "integer",
            #                 "description": "Maximum number of results to return (default 5)"
            #             }
            #         },
            #         "required": ["query"]
            #     }
            }
        ]

        # Build system prompt with context
        has_photo = context.get('has_photo', False)
        photo_context = "\n- USER HAS SENT A PHOTO! They want to save it as a memory." if has_photo else ""

        system_prompt = f"""You are a helpful assistant for a memories storage bot on Telegram.
Users can create events and store memories (photos and text) in them.

Current user context:
- Telegram ID: {context.get('telegram_id', 'unknown')}
- Username: {context.get('username', 'unknown')}
- First name: {context.get('first_name', 'unknown')}{photo_context}

Your job is to:
1. Understand what the user wants to do
2. Call the appropriate tool with the right parameters
3. Provide a friendly response based on the tool results

Available actions:
- create_event: Create a new event
- join_event: Join an existing event
- add_memory: Add a memory to an event (use this when user sends a photo!)
- list_events: Show user's events
- list_memories: Show memories from an event
- get_faq: Get help and instructions (use when user asks "how to", "help", "how do I", etc.)

IMPORTANT PHOTO HANDLING:
When the user has sent a photo (indicated above), they want to save it as a memory. Look for:
- Event names or IDs in their message: "sube a hackaton", "add to event #1", "save to birthday"
- If you can identify the event, use add_memory tool immediately
- Use list_events first if you need to find the event ID by name
- DO NOT use get_faq when they've sent a photo - they want ACTION, not help!

Examples with photos:
- "Sube a hackaton" + photo → list_events to find "hackaton", then add_memory to that event
- "Add to event #1" + photo → add_memory with event_id=1
- Photo only → ask which event they want to add it to

When user asks questions (WITHOUT photo) like:
- "How do I upload a photo?" → use get_faq with topic "upload_image"
- "How to invite someone?" → use get_faq with topic "invite_user"
- "Help" → use get_faq with topic "general"

When showing memories with images:
- The image_url field will contain a presigned URL that's valid for 1 hour
- You can include the URL in your response so users can view the photo
- Format: "📸 [View photo](URL)" in markdown

When you use a tool, wait for the result before responding to the user.
"""

        # Initialize message history for the conversation
        messages = [
            {
                "role": "user",
                "content": user_message
            }
        ]

        # Tool execution loop
        max_iterations = 5  # Prevent infinite loops
        iteration = 0

        while iteration < max_iterations:
            iteration += 1

            # Call Claude API with tools
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                system=system_prompt,
                tools=tools,
                messages=messages
            )

            # Check if Claude wants to use a tool
            tool_use_blocks = [block for block in response.content if block.type == "tool_use"]

            if not tool_use_blocks:
                # No tools needed, extract final text response
                text_blocks = [block for block in response.content if block.type == "text"]
                final_text = text_blocks[0].text if text_blocks else "Done!"
                print(f"[AGENT] Final response: {final_text}")
                return final_text

            # Claude wants to use tools - execute them
            print(f"[AGENT] Claude wants to use {len(tool_use_blocks)} tool(s)")

            # First, add Claude's response to messages
            messages.append({
                "role": "assistant",
                "content": response.content
            })

            # Execute each tool and collect results
            tool_results = []
            for tool_block in tool_use_blocks:
                tool_name = tool_block.name
                tool_input = tool_block.input
                tool_use_id = tool_block.id

                print(f"[AGENT] Executing tool: {tool_name}")
                print(f"[AGENT] Tool input: {json.dumps(tool_input, indent=2)}")

                # Execute the tool using the executor function
                if self.tool_executor:
                    try:
                        result = await self.tool_executor(tool_name, tool_input, context)
                        print(f"[AGENT] Tool result: {json.dumps(result, indent=2)}")
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_use_id,
                            "content": json.dumps(result)
                        })
                    except Exception as e:
                        print(f"[AGENT] Tool execution error: {e}")
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_use_id,
                            "content": json.dumps({"success": False, "message": f"Error: {str(e)}"})
                        })
                else:
                    # No executor set, return error
                    print(f"[AGENT] ERROR: Tool executor not configured!")
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_use_id,
                        "content": json.dumps({"success": False, "message": "Tool executor not configured"})
                    })

            # Add tool results to messages for next iteration
            messages.append({
                "role": "user",
                "content": tool_results
            })

            # Continue loop - Claude will process the tool results and either:
            # 1. Use more tools, or
            # 2. Provide a final text response

        # If we hit max iterations, return a fallback
        return "I've completed the requested actions."

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
