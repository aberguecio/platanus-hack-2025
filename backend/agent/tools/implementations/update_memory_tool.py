from typing import Dict, Any, Optional
from ..base_tool import BaseTool, ExecutionContext
from services import DatabaseService


class UpdateMemoryTool(BaseTool):
    """Tool for updating existing memories (text and/or image_description)"""

    def __init__(self):
        super().__init__(
            name="update_memory",
            description="Update the text content or image description of an existing memory. Useful for enriching memories with additional context after they've been created.",
            input_schema={
                "type": "object",
                "properties": {
                    "memory_id": {
                        "type": "integer",
                        "description": "ID of the memory to update",
                    },
                    "text": {
                        "type": "string",
                        "description": "New or additional text content for the memory (optional)",
                    },
                    "image_description": {
                        "type": "string",
                        "description": "New or enhanced image description (optional)",
                    },
                },
                "required": ["memory_id"],
            },
        )

    async def execute(
        self, tool_input: Dict[str, Any], ctx: ExecutionContext
    ) -> Dict[str, Any]:
        """Update an existing memory with new text or image_description"""

        memory_id = tool_input.get("memory_id")
        text = tool_input.get("text")
        image_desc = tool_input.get("image_description")

        print(f"[TOOL] update_memory - memory_id: {memory_id}")
        print(f"[TOOL] update_memory - text: {text[:50] if text else None}...")
        print(f"[TOOL] update_memory - image_description: {image_desc[:50] if image_desc else None}...")

        # Validate at least one field to update
        if text is None and image_desc is None:
            return {
                "success": False,
                "message": "Must provide at least text or image_description to update",
            }

        # Update memory
        memory = DatabaseService.update_memory(
            db=ctx.db,
            user=ctx.user,
            memory_id=memory_id,
            text=text,
            image_description=image_desc
        )

        if memory:
            updated_fields = []
            if text is not None:
                updated_fields.append("text")
            if image_desc is not None:
                updated_fields.append("image_description")

            return {
                "success": True,
                "message": f"Memory #{memory_id} updated ({', '.join(updated_fields)})",
            }
        else:
            return {
                "success": False,
                "message": f"Memory #{memory_id} not found or you don't have permission to update it",
            }

