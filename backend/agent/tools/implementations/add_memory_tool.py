from typing import Dict, Any
from ..base_tool import BaseTool, ExecutionContext
from services import DatabaseService
from enums import MediaTypeEnum


class AddMemoryTool(BaseTool):
    """Tool for adding memories (text and/or images) to events"""

    def __init__(self):
        super().__init__(
            name="add_memory",
            description="Add a memory (text and/or image) to an event",
            input_schema={
                "type": "object",
                "properties": {
                    "event_id": {
                        "type": "integer",
                        "description": "ID of the event",
                    },
                    "text": {
                        "type": "string",
                        "description": "Text content of the memory",
                    },
                    "has_image": {
                        "type": "boolean",
                        "description": "Whether this memory includes an image",
                    },
                },
                "required": ["event_id"],
            },
        )

    async def execute(
        self, tool_input: Dict[str, Any], ctx: ExecutionContext
    ) -> Dict[str, Any]:
        """Add a memory to an event, handling text and/or images"""

        event_id = tool_input.get("event_id")
        memory_text = tool_input.get("text")
        has_image = tool_input.get("has_image", False)

        # Handle image from context if available
        photo_file_id = ctx.photo_file_id
        image_url = None

        print(f"[TOOL] add_memory - event_id: {event_id}")
        print(f"[TOOL] add_memory - memory_text: {memory_text}")
        print(f"[TOOL] add_memory - has_image param: {has_image}")
        print(f"[TOOL] add_memory - context.has_photo: {ctx.has_photo}")
        print(f"[TOOL] add_memory - photo_file_id from context: {photo_file_id}")
        print(f"[TOOL] add_memory - message_id from context: {ctx.message_id}")

        # Variables for image handling
        image_description = None
        image_data_for_description = None

        # If has_image is True but no photo_file_id in current context,
        # search for recent photo in conversation history
        if has_image and not photo_file_id and ctx.conversation_id:
            print(f"[TOOL] Searching for recent photo in conversation history...")
            from models import Message, MessageDirectionEnum

            # Get the last 5 USER messages with photos
            recent_messages = ctx.db.query(Message).filter(
                Message.conversation_id == ctx.conversation_id,
                Message.direction == MessageDirectionEnum.USER,
                Message.photo_s3_url.isnot(None)
            ).order_by(Message.created_at.desc()).limit(5).all()

            if recent_messages:
                # Use the most recent photo
                image_url = recent_messages[0].photo_s3_url
                print(f"[TOOL] Found recent photo in history: {image_url}")

                # Download image from S3 for description generation
                if ctx.s3_service and ctx.image_service:
                    try:
                        print(f"[TOOL] Downloading image from S3 for description...")
                        image_data_for_description = await ctx.s3_service.download_image(image_url)
                        print(f"[TOOL] Image downloaded from S3: {len(image_data_for_description)} bytes")
                    except Exception as download_error:
                        print(f"[TOOL] Error downloading image from S3: {download_error}")
            else:
                print(f"[TOOL] No recent photo found in history")

        # If there's a photo_file_id in current context, download from Telegram and upload to S3
        if photo_file_id and not image_url:
            if not ctx.telegram_service:
                print("[TOOL] WARNING: telegram_service not available")
                image_url = photo_file_id  # Fallback to file_id
            elif not ctx.s3_service:
                print("[TOOL] WARNING: s3_service not available")
                image_url = photo_file_id  # Fallback to file_id
            else:
                try:
                    print(f"[TOOL] Downloading photo from Telegram...")
                    image_data = await ctx.telegram_service.download_file(photo_file_id)
                    print(f"[TOOL] Photo downloaded, size: {len(image_data)} bytes")

                    # Store image data for description generation
                    image_data_for_description = image_data

                    # Upload to S3
                    print(f"[TOOL] Uploading to S3...")
                    image_url = await ctx.s3_service.upload_image(
                        image_data, f"memory_{event_id}_{photo_file_id[:20]}.jpg"
                    )
                    print(f"[TOOL] Image uploaded to S3: {image_url}")
                except Exception as img_error:
                    print(f"[TOOL] Error handling image: {img_error}")
                    import traceback

                    traceback.print_exc()
                    # Fallback to file_id if download/upload fails
                    image_url = photo_file_id

        # Generate image description if we have image data
        if image_data_for_description and ctx.image_service:
            try:
                print(f"[TOOL] Generating image description with Claude Vision...")
                image_description = ctx.image_service.describe_image(image_data_for_description)
                print(f"[TOOL] Image description generated: {image_description[:100]}...")
            except Exception as desc_error:
                print(f"[TOOL] Error generating image description: {desc_error}")
                import traceback
                traceback.print_exc()

        # Add memory to database (linked to the current message if available)
        memory = DatabaseService.add_memory(
            db=ctx.db,
            user=ctx.user,
            event_id=event_id,
            text=memory_text,
            s3_url=image_url,
            image_description=image_description,
            media_type=MediaTypeEnum.IMAGE if image_url else None,
            message_id=ctx.message_id
        )

        if memory:
            result_msg = f"Memory added to event #{event_id}!"
            if image_url:
                if image_url.startswith("http"):
                    result_msg += f" (photo saved from history)" if has_image and not photo_file_id else f" (photo uploaded to S3)"
                else:
                    result_msg += f" (photo saved as Telegram file_id)"
            return {"success": True, "message": result_msg}
        else:
            return {
                "success": False,
                "message": "Could not add memory. Make sure you're in this event.",
            }

