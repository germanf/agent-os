import json
from pathlib import Path

from dashboard.mcp.server import MCPServer, ToolDef
from dashboard.workflow import WorkflowEngine, parse_workflow

WORKFLOWS_DIR = Path(__file__).parent.parent / "data" / "workflows"


class WorkflowsMCPServer(MCPServer):
    name = "workflows"
    version = "1.0.0"

    async def list_tools(self) -> list[ToolDef]:
        return [
            ToolDef(name="list_workflows", description="List available workflow definitions",
                    input_schema={"type": "object", "properties": {}}),
            ToolDef(name="get_workflow", description="Get a workflow definition by name",
                    input_schema={"type": "object", "properties": {
                        "name": {"type": "string"},
                    }, "required": ["name"]}),
            ToolDef(name="get_workflow_status", description="Get step-level status for a workflow",
                    input_schema={"type": "object", "properties": {
                        "name": {"type": "string"}, "session_id": {"type": "string"},
                    }, "required": ["name"]}),
        ]

    async def call_tool(self, name: str, args: dict):
        if name == "list_workflows":
            if not WORKFLOWS_DIR.exists():
                return []
            return sorted(f.stem for f in WORKFLOWS_DIR.iterdir() if f.suffix in (".json", ".yaml", ".yml"))
        elif name == "get_workflow":
            file = self._find_workflow(args["name"])
            if not file:
                raise ValueError(f"Workflow not found: {args['name']}")
            return json.loads(file.read_text()) if file.suffix == ".json" else file.read_text()
        elif name == "get_workflow_status":
            file = self._find_workflow(args["name"])
            if not file:
                raise ValueError(f"Workflow not found: {args['name']}")
            wf = parse_workflow(file)
            engine = WorkflowEngine(wf, args.get("session_id", ""))
            return engine.summary()
        raise ValueError(f"Unknown tool: {name}")

    @staticmethod
    def _find_workflow(name: str) -> Path | None:
        for ext in (".json", ".yaml", ".yml"):
            p = WORKFLOWS_DIR / f"{name}{ext}"
            if p.exists():
                return p
        return None
