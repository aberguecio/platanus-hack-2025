"""
Auto-register all tools when this module is imported
"""
from ..tool_registry import get_registry
from .create_event_tool import CreateEventTool
from .join_event_tool import JoinEventTool
from .add_memory_tool import AddMemoryTool
from .list_events_tool import ListEventsTool
from .list_memories_tool import ListMemoriesTool
from .get_faq_tool import GetFaqTool


def register_all_tools():
    """Register all available tools in the registry"""
    registry = get_registry()

    # Register all tools
    registry.register(CreateEventTool())
    registry.register(JoinEventTool())
    registry.register(AddMemoryTool())
    registry.register(ListEventsTool())
    registry.register(ListMemoriesTool())
    registry.register(GetFaqTool())

    print(f"[TOOLS] All tools registered successfully")


# Auto-register when module is imported
register_all_tools()
