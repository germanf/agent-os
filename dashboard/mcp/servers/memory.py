from dashboard.mcp.server import MCPServer, ResourceDef, ToolDef
from dashboard.memory import OrgMemoryStore, ProjectMemoryStore


class MemoryMCPServer(MCPServer):
    name = "memory"
    version = "1.0.0"

    def __init__(self):
        self._project = ProjectMemoryStore()
        self._org = OrgMemoryStore()

    async def list_tools(self) -> list[ToolDef]:
        return [
            ToolDef(name="store_project_memory", description="Store a key-value memory for a project",
                    input_schema={"type": "object", "properties": {
                        "project_id": {"type": "integer"}, "key": {"type": "string"}, "value": {"type": "string"},
                    }, "required": ["project_id", "key", "value"]}),
            ToolDef(name="get_project_memory", description="Get a memory value by key for a project",
                    input_schema={"type": "object", "properties": {
                        "project_id": {"type": "integer"}, "key": {"type": "string"},
                    }, "required": ["project_id", "key"]}),
            ToolDef(name="list_project_memories", description="List all memories for a project",
                    input_schema={"type": "object", "properties": {
                        "project_id": {"type": "integer"},
                    }, "required": ["project_id"]}),
            ToolDef(name="store_org_memory", description="Store an organizational memory entry",
                    input_schema={"type": "object", "properties": {
                        "key": {"type": "string"}, "value": {"type": "string"},
                        "source_project_id": {"type": "integer"}, "tags": {"type": "string"},
                    }, "required": ["key", "value"]}),
            ToolDef(name="search_org_memory", description="Search organizational memories",
                    input_schema={"type": "object", "properties": {
                        "query": {"type": "string"},
                    }, "required": ["query"]}),
        ]

    async def call_tool(self, name: str, args: dict):
        if name == "store_project_memory":
            return await self._project.set(args["project_id"], args["key"], args["value"])
        elif name == "get_project_memory":
            return await self._project.get(args["project_id"], args["key"])
        elif name == "list_project_memories":
            return await self._project.list(args["project_id"])
        elif name == "store_org_memory":
            return await self._org.set(args["key"], args["value"],
                                        args.get("source_project_id"), args.get("tags", ""))
        elif name == "search_org_memory":
            return await self._org.search(args["query"])
        raise ValueError(f"Unknown tool: {name}")

    async def list_resources(self) -> list[ResourceDef]:
        return [
            ResourceDef(uri="memory://org/summary", name="Org Memory Summary",
                        description="Summary of all organizational memories"),
        ]

    async def read_resource(self, uri: str) -> str:
        if uri == "memory://org/summary":
            entries = await self._org.list_all()
            return "\n".join(f"{e['key']}: {e['value'][:200]}" for e in entries[:50])
        raise ValueError(f"Unknown resource: {uri}")
