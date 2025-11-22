from typing import Dict, Any
from ..base_tool import BaseTool, ExecutionContext


class GetFaqTool(BaseTool):
    """Tool for getting help and instructions about bot features"""

    def __init__(self):
        super().__init__(
            name="get_faq",
            description="Get help and instructions about how to use the bot features",
            input_schema={
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "The help topic: 'upload_image', 'invite_user', 'create_event', 'add_memory', 'general'",
                        "enum": [
                            "upload_image",
                            "invite_user",
                            "create_event",
                            "add_memory",
                            "general",
                        ],
                    }
                },
                "required": ["topic"],
            },
        )

    async def execute(
        self, tool_input: Dict[str, Any], ctx: ExecutionContext
    ) -> Dict[str, Any]:
        """Get FAQ content for a specific topic"""

        topic = tool_input.get("topic", "general")

        faq_content = {
            "upload_image": {
                "title": "How to upload an image/photo",
                "steps": [
                    "1. First, create an event or make sure you're part of one (use 'list my events' to check)",
                    "2. Send a photo directly to the bot (using Telegram's photo upload)",
                    "3. You can optionally add a caption to the photo",
                    "4. The bot will ask which event to add it to, or you can say 'add this to event #X'",
                    "5. The photo will be stored as a memory in that event!",
                ],
                "example": "Just send a photo and say 'add this to event #1' or 'save this memory to hackaton event'",
            },
            "invite_user": {
                "title": "How to invite people to an event",
                "steps": [
                    "Currently, each user manages their own events independently.",
                    "To share an event:",
                    "1. Tell your friend the event ID (e.g., #1)",
                    "2. They can say 'join event #1' to join",
                    "3. Once joined, they can add their own memories to the event",
                    "4. Both of you will see all memories in the shared event!",
                ],
                "note": "Event IDs are numbers like #1, #2, #3, etc.",
            },
            "create_event": {
                "title": "How to create an event",
                "steps": [
                    "Just tell me what event you want to create!",
                    "Examples:",
                    "- 'Create event Birthday Party'",
                    "- 'Create a new event named Summer Trip'",
                    "- 'New event: Graduation 2025'",
                    "You can optionally add a date:",
                    "- 'Create event Christmas on 2025-12-25'",
                    "You'll automatically be added to events you create!",
                ],
            },
            "add_memory": {
                "title": "How to add a memory",
                "steps": [
                    "You can add both text and photo memories:",
                    "Text memory:",
                    "- 'Add memory to event #1: Had a great time!'",
                    "- 'Save to hackaton: Met amazing people'",
                    "Photo memory:",
                    "- Send a photo and say 'add to event #1'",
                    "- Or send photo with caption: 'for event #2'",
                    "Combined:",
                    "- Send a photo with a descriptive caption",
                ],
            },
            "general": {
                "title": "General Help - What I can do",
                "capabilities": [
                    "📅 Create events: 'Create event [name]'",
                    "👥 Join events: 'Join event #1'",
                    "💭 Add memories: 'Add memory to event #1: [text]'",
                    "📸 Upload photos: Send a photo directly",
                    "📋 List your events: 'Show my events' or 'List events'",
                    "🔍 View memories: 'Show memories from event #1'",
                ],
                "tips": [
                    "Events have IDs like #1, #2, #3",
                    "You can have multiple events",
                    "Share event IDs with friends so they can join",
                    "Photos and text are both supported",
                ],
            },
        }

        faq = faq_content.get(topic, faq_content["general"])
        return {"success": True, "faq": faq, "topic": topic}

