from dashboard.headroom_memory import HeadroomSessionMemory
from dashboard.mcp.server import MCPServer, ResourceDef, ToolDef
from dashboard.memory import OrgMemoryStore, ProjectMemoryStore


class MemoryMCPServer(MCPServer):
    name = "memory"
    version = "1.0.0"

    def __init__(self):
        self._project = ProjectMemoryStore()
        self._org = OrgMemoryStore()
        self._headroom = HeadroomSessionMemory()

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

    async def _headroom_remember(self, content: str, user_id: str) -> None:
        if not self._headroom.available:
            await self._headroom.ensure_ready()
        if not self._headroom.available:
            return
        try:
            await self._headroom.remember(content, user_id=user_id)
        except Exception:
            pass

    async def _headroom_recall(self, query: str, user_id: str) -> list:
        if not self._headroom.available:
            await self._headroom.ensure_ready()
        if not self._headroom.available:
            return []
        try:
            return await self._headroom.recall(query, user_id=user_id) or []
        except Exception:
            return []

    async def call_tool(self, name: str, args: dict):
        if name == "store_project_memory":
            result = await self._project.set(args["project_id"], args["key"], args["value"])
            await self._headroom_remember(
                f"project:{args['project_id']}:{args['key']}={args['value']}",
                user_id=f"project-{args['project_id']}",
            )
            return result
        elif name == "get_project_memory":
            return await self._project.get(args["project_id"], args["key"])
        elif name == "list_project_memories":
            return await self._project.list(args["project_id"])
        elif name == "store_org_memory":
            result = await self._org.set(args["key"], args["value"],
                                         args.get("source_project_id"), args.get("tags", ""))
            await self._headroom_remember(
                f"org:{args['key']}={args['value']}",
                user_id="org",
            )
            return result
        elif name == "search_org_memory":
            sqlite_hits = await self._org.search(args["query"])
            headroom_hits = await self._headroom_recall(args["query"], user_id="org")
            seen = {h.get("key") for h in sqlite_hits if h.get("key")}
            merged = list(sqlite_hits)
            for hit in headroom_hits if isinstance(headroom_hits, list) else []:
                if isinstance(hit, dict):
                    key = hit.get("key") or hit.get("id")
                    if key and key not in seen:
                        merged.append({
                            "key": key,
                            "value": hit.get("content") or hit.get("value") or "",
                            "score": hit.get("score"),
                        })
                        seen.add(key)
            return merged
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
