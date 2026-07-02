from dashboard.kanban import complete_task, create_task, list_tasks, show_task
from dashboard.mcp.server import MCPServer, ToolDef


class KanbanMCPServer(MCPServer):
    name = "kanban"
    version = "1.0.0"

    async def list_tools(self) -> list[ToolDef]:
        return [
            ToolDef(name="list_tasks", description="List kanban tasks, optionally filtered by status",
                    input_schema={"type": "object", "properties": {
                        "status": {"type": "string", "description": "Filter by status (todo, in_progress, done)"},
                    }}),
            ToolDef(name="create_task", description="Create a new kanban task",
                    input_schema={"type": "object", "properties": {
                        "title": {"type": "string"}, "body": {"type": "string"},
                        "assignee": {"type": "string"}, "priority": {"type": "integer"},
                    }, "required": ["title"]}),
            ToolDef(name="complete_task", description="Mark a kanban task as complete",
                    input_schema={"type": "object", "properties": {
                        "task_id": {"type": "string"},
                    }, "required": ["task_id"]}),
            ToolDef(name="show_task", description="Get details of a specific task",
                    input_schema={"type": "object", "properties": {
                        "task_id": {"type": "string"},
                    }, "required": ["task_id"]}),
        ]

    async def call_tool(self, name: str, args: dict):
        if name == "list_tasks":
            return await list_tasks(status=args.get("status"))
        elif name == "create_task":
            result = await create_task(
                title=args["title"], body=args.get("body"),
                assignee=args.get("assignee"), priority=args.get("priority"),
            )
            return result
        elif name == "complete_task":
            return await complete_task(args["task_id"])
        elif name == "show_task":
            return await show_task(args["task_id"])
        raise ValueError(f"Unknown tool: {name}")
