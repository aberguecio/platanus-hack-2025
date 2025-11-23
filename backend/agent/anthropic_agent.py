import os
import json
from typing import Optional
from anthropic import Anthropic
from .base import LLMAgent
from .tools import get_registry, ExecutionContext
from .prompts import get_prompt_builder

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
        self.prompt_builder = get_prompt_builder()

    async def process_message(
        self,
        user_message: str,
        ctx: ExecutionContext
    ) -> str:
        """
        Process message using Claude with tool calling for structured actions.
        Returns the final text response after executing all necessary tools.

        Args:
            user_message: The message from the user
            ctx: ExecutionContext with all dependencies (db, user, services, metadata)

        Returns:
            Final text response to send back to the user
        """
        # Handle empty messages
        if not user_message or not user_message.strip():
            return "Please send me a message!"

        print(f"\n[AGENT] Processing message: {user_message}")

        # Get tools dynamically from registry
        registry = get_registry()
        tools = registry.get_schemas()

        # Build system prompt with context using the prompt builder
        system_prompt = self.prompt_builder.build_system_prompt(
            telegram_id=ctx.telegram_id,
            username=ctx.username,
            first_name=ctx.first_name,
            has_photo=ctx.has_photo
        )

        print(f"[AGENT] System prompt length: {len(system_prompt)} chars")

        # Initialize message history for the conversation
        messages = []

        # Include conversation history for context (if available)
        if ctx.conversation_history and len(ctx.conversation_history) > 0:
            for msg in ctx.conversation_history:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })

        # Add current user message
        messages.append({
            "role": "user",
            "content": user_message
        })

        print(f"[AGENT] 🎃 Total messages in context: {len(messages)}")

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

                # Execute the tool using the registry
                try:
                    result = await registry.execute(tool_name, tool_input, ctx)
                    print(f"[AGENT] Tool result: {json.dumps(result, indent=2)}")
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_use_id,
                        "content": json.dumps(result)
                    })
                except Exception as e:
                    print(f"[AGENT] Tool execution error: {e}")
                    import traceback
                    traceback.print_exc()
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_use_id,
                        "content": json.dumps({"success": False, "message": f"Error: {str(e)}"})
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
