"""
Auto-register all tools when this module is imported
"""
from ..tool_registry import get_registry
from .create_event_tool import CreateEventTool
from .join_event_tool import JoinEventTool
from .join_event_invite_tool import JoinEventInviteTool
from .add_memory_tool import AddMemoryTool
from .list_events_tool import ListEventsTool
from .list_memories_tool import ListMemoriesTool
from .get_faq_tool import GetFaqTool
from .generate_invite_link_tool import GenerateInviteLinkTool
from .summarize_event_tool import SummarizeEventTool


def register_all_tools():
    """Register all available tools in the registry"""
    registry = get_registry()

    # Register all tools
    registry.register(CreateEventTool())
    registry.register(JoinEventTool())
    registry.register(JoinEventInviteTool())
    registry.register(AddMemoryTool())
    registry.register(ListEventsTool())
    registry.register(ListMemoriesTool())
    registry.register(GetFaqTool())
    registry.register(GenerateInviteLinkTool())
    registry.register(SummarizeEventTool())

    print(f"[TOOLS] All tools registered successfully")


# Auto-register when module is imported
register_all_tools()
