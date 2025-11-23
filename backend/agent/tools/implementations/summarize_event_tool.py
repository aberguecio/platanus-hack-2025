from typing import Dict, Any
from ..base_tool import BaseTool, ExecutionContext
from services import DatabaseService


class SummarizeEventTool(BaseTool):
    """Tool for generating a comprehensive summary of an event with all its memories"""

    def __init__(self):
        super().__init__(
            name="summarize_event",
            description="Generate a comprehensive summary of an event including all memories, photos, and insights",
            input_schema={
                "type": "object",
                "properties": {
                    "event_id": {
                        "type": "integer",
                        "description": "ID of the event to summarize",
                    },
                },
                "required": ["event_id"],
            },
        )

    async def execute(
        self, tool_input: Dict[str, Any], ctx: ExecutionContext
    ) -> Dict[str, Any]:
        """Generate a comprehensive event summary"""

        event_id = tool_input.get("event_id")

        print(f"[SUMMARIZE_EVENT] Generating summary for event #{event_id}")

        # Get event details
        event = DatabaseService.get_event(ctx.db, event_id)

        if not event:
            return {"success": False, "message": f"Event #{event_id} not found."}

        # Check if user is member of event
        if event not in ctx.user.events:
            return {
                "success": False,
                "message": "You don't have access to this event.",
            }

        # Get all memories from the event
        memories = DatabaseService.list_event_memories(ctx.db, event_id)

        if not memories:
            return {
                "success": True,
                "message": f"El evento '{event.name}' aún no tiene memorias guardadas.",
                "event_name": event.name,
                "event_description": event.description,
                "memories_count": 0,
            }

        # Collect statistics
        total_memories = len(memories)
        memories_with_photos = sum(1 for m in memories if m.s3_url)
        memories_with_text = sum(1 for m in memories if m.text)
        memories_with_embeddings = sum(1 for m in memories if m.embedding is not None)

        # Collect all texts and descriptions
        all_texts = []
        photo_descriptions = []

        for memory in memories:
            if memory.text:
                all_texts.append(memory.text)
            if memory.s3_url and memory.text:
                # If there's both image and text, likely the text is a description
                photo_descriptions.append(memory.text)

        # Generate presigned URLs for photos
        photo_urls = []
        if memories_with_photos > 0:
            for memory in memories:
                if memory.s3_url:
                    presigned_url = ctx.s3_service.generate_presigned_url(memory.s3_url)
                    photo_urls.append({
                        "url": presigned_url,
                        "description": memory.text or "Sin descripción",
                        "created_at": memory.created_at.isoformat() if memory.created_at else None
                    })

        # Build the summary
        summary_data = {
            "success": True,
            "event_name": event.name,
            "event_description": event.description,
            "event_date": event.event_date.isoformat() if event.event_date else None,
            "invite_code": event.invite_code,
            "statistics": {
                "total_memories": total_memories,
                "photos": memories_with_photos,
                "text_memories": memories_with_text,
                "with_embeddings": memories_with_embeddings,
            },
            "photos": photo_urls,
            "text_memories": all_texts,
            "photo_descriptions": photo_descriptions,
        }

        print(f"[SUMMARIZE_EVENT] Summary generated: {total_memories} memories, {memories_with_photos} photos")

        return summary_data
