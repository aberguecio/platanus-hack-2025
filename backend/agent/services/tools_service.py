class ToolsService:
    def __init__(self):
        self.tools = []

    def get_tools(self):
        return self.tools

    def add_tool(self, tool):
        self.tools.append(tool)