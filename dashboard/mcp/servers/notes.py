import os

from dashboard.config import VAULT_DIR
from dashboard.mcp.server import MCPServer, ResourceDef, ToolDef


def _build_tree(path: str, prefix: str = "") -> list[dict]:
    result = []
    try:
        for name in sorted(os.listdir(path)):
            full = os.path.join(path, name)
            rel = os.path.relpath(full, VAULT_DIR) if VAULT_DIR else name
            if name.endswith(".md"):
                with open(full) as f:
                    first_line = f.readline().strip()
                result.append({"name": name, "path": rel, "title": first_line.lstrip("# ") or name[:-3]})
            elif os.path.isdir(full):
                children = _build_tree(full, prefix + name + "/")
                if children:
                    result.append({"name": name, "path": rel, "children": children})
    except PermissionError:
        pass
    return result


def _read_note(path: str) -> str | None:
    full = os.path.join(VAULT_DIR, path) if VAULT_DIR else path
    if not os.path.isfile(full) or not full.endswith(".md"):
        return None
    with open(full) as f:
        return f.read()


class NotesMCPServer(MCPServer):
    name = "notes"
    version = "1.0.0"

    async def list_tools(self) -> list[ToolDef]:
        return [
            ToolDef(name="search_notes", description="Search notes by path substring",
                    input_schema={"type": "object", "properties": {
                        "query": {"type": "string"},
                    }, "required": ["query"]}),
            ToolDef(name="read_note", description="Read a note by its relative path",
                    input_schema={"type": "object", "properties": {
                        "path": {"type": "string"},
                    }, "required": ["path"]}),
        ]

    async def call_tool(self, name: str, args: dict):
        if name == "search_notes":
            query = args["query"].lower()
            results = []
            if VAULT_DIR and os.path.isdir(VAULT_DIR):
                for root, dirs, files in os.walk(VAULT_DIR):
                    for f in files:
                        if f.endswith(".md") and query in f.lower():
                            rel = os.path.relpath(os.path.join(root, f), VAULT_DIR)
                            results.append({"path": rel, "name": f})
            return results[:20]
        elif name == "read_note":
            content = _read_note(args["path"])
            if content is None:
                raise ValueError(f"Note not found: {args['path']}")
            return {"path": args["path"], "content": content[:5000]}
        raise ValueError(f"Unknown tool: {name}")

    async def list_resources(self) -> list[ResourceDef]:
        resources = [ResourceDef(uri="notes://tree", name="Notes Tree",
                                 description="Full vault tree structure")]
        if VAULT_DIR and os.path.isdir(VAULT_DIR):
            for root, dirs, files in os.walk(VAULT_DIR):
                for f in files:
                    if f.endswith(".md"):
                        rel = os.path.relpath(os.path.join(root, f), VAULT_DIR)
                        resources.append(ResourceDef(
                            uri=f"notes://content/{rel}", name=f"Note: {rel[:-3]}",
                            description=f"Content of {rel}",
                        ))
        return resources

    async def read_resource(self, uri: str) -> str:
        if uri == "notes://tree":
            tree = _build_tree(str(VAULT_DIR)) if VAULT_DIR else []
            return "\n".join(item["name"] for item in tree[:100])
        if uri.startswith("notes://content/"):
            path = uri[len("notes://content/"):]
            content = _read_note(path)
            return content or "Note not found"
        raise ValueError(f"Unknown resource: {uri}")
