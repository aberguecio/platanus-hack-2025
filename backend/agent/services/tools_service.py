from tools.create_event_tool import CreateEventTool# Service to manage and handle the tools of the agent

class ToolsService:
    def __init__(self):
        self.tools = []

    def get_tools(self):
        return self.tools

    def add_tool(self, tool):
        self.tools.append(tool)

    def 