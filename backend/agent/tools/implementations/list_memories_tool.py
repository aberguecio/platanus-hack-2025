from typing import Dict, Any
from ..base_tool import BaseTool, ExecutionContext
from services import DatabaseService


class ListMemoriesTool(BaseTool):
    """Tool for listing memories from a specific event"""

    def __init__(self):
        super().__init__(
            name="list_memories",
            description="List memories from a specific event",
            input_schema={
                "type": "object",
                "properties": {
                    "event_id": {
                        "type": "integer",
                        "description": "ID of the event",
                    },
                },
                "required": ["event_id"],
            },
        )

    async def execute(
        self, tool_input: Dict[str, Any], ctx: ExecutionContext
    ) -> Dict[str, Any]:
        """List all memories from an event"""

        event_id = tool_input.get("event_id")
        memories = DatabaseService.list_event_memories(ctx.db, event_id)

        if not memories:
            return {
                "success": True,
                "message": f"No memories in event #{event_id} yet.",
                "memories": [],
            }

        memories_list = []
        for m in memories:
            # Generate presigned URL if image is stored in S3
            image_url = m.image_url
            print(f"[TOOL] list_memories - original image_url: {image_url}")

            if image_url and image_url.startswith("s3://"):
                if ctx.s3_service:
                    presigned_url = ctx.s3_service.generate_presigned_url(
                        image_url, expiration=3600
                    )
                    print(
                        f"[TOOL] list_memories - presigned URL generated: {presigned_url[:100]}..."
                    )
                    image_url = presigned_url
                else:
                    print("[TOOL] WARNING: s3_service not available for presigned URL")

            memories_list.append(
                {
                    "id": m.id,
                    "text": m.text or "(photo only)",
                    "user": m.user.first_name,
                    "image_url": image_url,
                    "has_image": bool(m.image_url),
                    "created_at": m.created_at.isoformat() if m.created_at else None,
                }
            )

        return {
            "success": True,
            "message": "Memories retrieved",
            "memories": memories_list,
            "count": len(memories_list),
        }

