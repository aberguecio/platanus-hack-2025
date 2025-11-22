from typing import Dict, List, Optional, Any
from .base_tool import BaseTool, ExecutionContext


class ToolRegistry:
    """Registry/Factory for managing all available tools"""

    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """Register a tool in the registry"""
        self._tools[tool.name] = tool
        print(f"[REGISTRY] Registered tool: {tool.name}")

    def get(self, name: str) -> Optional[BaseTool]:
        """Get a tool by name"""
        return self._tools.get(name)

    def get_all(self) -> List[BaseTool]:
        """Return all registered tools"""
        return list(self._tools.values())

    def get_schemas(self) -> List[Dict[str, Any]]:
        """Return the schemas of all tools for Anthropic API"""
        return [tool.to_schema() for tool in self._tools.values()]

    async def execute(
        self, tool_name: str, tool_input: Dict[str, Any], ctx: ExecutionContext
    ) -> Dict[str, Any]:
        """
        Execute a tool by name

        Args:
            tool_name: Name of the tool to execute
            tool_input: Input parameters for the tool
            ctx: Execution context with all dependencies

        Returns:
            Dict with execution result
        """
        tool = self.get(tool_name)

        if not tool:
            return {"success": False, "message": f"Unknown tool: {tool_name}"}

        try:
            print(f"[REGISTRY] Executing tool: {tool_name}")
            result = await tool.execute(tool_input, ctx)
            print(f"[REGISTRY] Tool {tool_name} completed successfully")
            return result
        except Exception as e:
            print(f"[REGISTRY] Tool {tool_name} execution error: {e}")
            import traceback

            traceback.print_exc()
            return {"success": False, "message": f"Tool execution error: {str(e)}"}


# Global registry instance
_registry = ToolRegistry()


def get_registry() -> ToolRegistry:
    """Get the global registry instance"""
    return _registry

