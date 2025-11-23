import os
import json
import base64
from typing import Optional, Dict, Any, List
from anthropic import Anthropic
from .base import LLMAgent
from .tools import get_registry, ExecutionContext
from .prompts.prompt_builder_v2 import get_prompt_builder

class AnthropicAgent(LLMAgent):
    """
    Anthropic Claude implementation of the LLM agent.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is required")

        self.client = Anthropic(api_key=self.api_key)

        self.prompt_builder = get_prompt_builder()
        self.model = self.prompt_builder.get_config("settings", {}).get("model", "claude-sonnet-4-5-20250929")

    async def _build_message_content(
        self, 
        text: str, 
        photo_file_id: Optional[str], 
        has_video: bool,
        video_file_id: Optional[str],
        telegram_service
    ) -> Any:
        """
        Build message content, handling text, photos, and videos.
        """
        # If no photo and no video, just return text
        if not photo_file_id and not has_video:
            return text

        content = []

        # Handle video
        if has_video:
            # Add text indicator for video
            video_text = "[VIDEO ADJUNTO: El usuario ha enviado un video. Usa add_memory con has_video=True para guardarlo.]"
            if video_file_id:
                video_text += f"\n[VIDEO_FILE_ID: {video_file_id}]"
            
            content.append({
                "type": "text",
                "text": video_text
            })

        # Handle photo
        if photo_file_id:
            try:
                # Download and encode photo
                image_data = await self._download_and_encode_photo(photo_file_id, telegram_service)
                
                # Detect media type
                media_type = self._detect_image_format(image_data)
                
                # Add image block
                content.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": media_type,
                        "data": image_data.decode('utf-8')
                    }
                })
            except Exception as e:
                print(f"[AGENT] Error processing photo: {e}")
                content.append({
                    "type": "text",
                    "text": "[FOTO ADJUNTA: Error al procesar la imagen para visualización]"
                })

        # Add text content if present
        if text:
            content.append({
                "type": "text",
                "text": text
            })
            
        return content

    async def _download_and_encode_photo(self, file_id: str, telegram_service) -> bytes:
        """
        Download photo from Telegram.
        """
        try:
            print(f"[AGENT] Downloading photo from Telegram: {file_id}")
            image_bytes = await telegram_service.download_file(file_id)
            print(f"[AGENT] Photo downloaded, size: {len(image_bytes)} bytes")
            return image_bytes
        except Exception as e:
            print(f"[AGENT] Error downloading photo: {e}")
            raise e

    @staticmethod
    def _detect_image_format(image_bytes: bytes) -> str:
        """Detect image format from magic bytes."""
        if image_bytes[:2] == b'\xff\xd8':
            return "image/jpeg"
        elif image_bytes[:8] == b'\x89PNG\r\n\x1a\n':
            return "image/png"
        elif image_bytes[:4] == b'RIFF' and image_bytes[8:12] == b'WEBP':
            return "image/webp"
        elif image_bytes[:6] in (b'GIF87a', b'GIF89a'):
            return "image/gif"
        else:
            return "image/jpeg"  # Default

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

        # Build system prompt with new V2 builder (always include examples)
        system_prompt = self.prompt_builder.build_system_prompt(
            telegram_id=ctx.telegram_id,
            username=ctx.username,
            first_name=ctx.first_name,
            has_photo=ctx.has_photo,
            has_video=ctx.has_video,
            conversation_history=ctx.conversation_history,
            include_examples=True  # Always include for consistent behavior
        )

        print(f"[AGENT] System prompt length: {len(system_prompt)} chars")

        # Initialize message history with smart formatting
        messages = []

        # Use the new context manager to format conversation history
        if ctx.conversation_history and len(ctx.conversation_history) > 0:
            formatted_history = self.prompt_builder.format_conversation_history(
                ctx.conversation_history,
                total_message_count=len(ctx.conversation_history)
            )
            messages.extend(formatted_history)

        # Add current user message (with photo if present)
        # For batch processing, add info about additional photos
        if ctx.is_batch and ctx.batch_photos and len(ctx.batch_photos) > 1:
            # Build list of all photo file_ids for the agent
            photo_ids = [photo["file_id"] for photo in ctx.batch_photos]
            batch_info = f"\n\n[SISTEMA: El usuario envió {len(ctx.batch_photos)} fotos. Debes guardar TODAS usando add_memory con estos photo_file_id:\n"
            for i, file_id in enumerate(photo_ids, 1):
                batch_info += f"- Foto {i}: {file_id}\n"
            batch_info += "Usa el parámetro 'photo_file_id' en add_memory para especificar cada foto.]"
            user_message_with_batch = user_message + batch_info
        else:
            user_message_with_batch = user_message

        current_message_content = await self._build_message_content(
            user_message_with_batch,
            ctx.photo_file_id,
            ctx.has_video,
            ctx.video_file_id,
            ctx.telegram_service
        )

        messages.append({
            "role": "user",
            "content": current_message_content
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

    async def send_message(
        self,
        messages: list,
        system_prompt: Optional[str] = None,
        max_tokens: int = 2048
    ) -> dict:
        """
        Send messages to Claude with optional system prompt.
        Returns response in format: {"content": [{"text": "..."}]}
        
        Args:
            messages: List of message dicts with "role" and "content" keys
            system_prompt: Optional system prompt
            max_tokens: Maximum tokens for response
            
        Returns:
            Dict with "content" key containing list of content blocks
        """
        kwargs = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": messages
        }
        
        if system_prompt:
            kwargs["system"] = system_prompt
            
        response = self.client.messages.create(**kwargs)
        
        # Convert response to expected format
        content = []
        for block in response.content:
            if block.type == "text":
                content.append({"text": block.text})
            # Handle other block types if needed
        
        return {"content": content}
