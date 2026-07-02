from dashboard.mcp.server import registry


async def discover_mcp_tools() -> list[dict]:
    tools = await registry.list_all_tools()
    return [
        {"server": server_name, "name": t.name, "description": t.description, "input_schema": t.input_schema}
        for server_name, t in tools
    ]


async def discover_mcp_resources() -> list[dict]:
    resources = await registry.list_all_resources()
    return [
        {"server": server_name, "uri": r.uri, "name": r.name, "description": r.description, "mime_type": r.mime_type}
        for server_name, r in resources
    ]


async def format_mcp_manifest() -> str:
    tools = await discover_mcp_tools()
    if not tools:
        return ""
    lines = ["## Available MCP Tools", ""]
    for t in tools:
        desc = t["description"][:120] + "..." if len(t["description"]) > 120 else t["description"]
        lines.append(f"- **{t['server']}/{t['name']}**: {desc}")
        schema = t["input_schema"]
        if schema and schema.get("properties"):
            params = ", ".join(schema["properties"].keys())
            lines[-1] += f"  Parameters: {params}"
    lines.append("")
    lines.append("Call these tools via your tool-use mechanism when appropriate.")
    return "\n".join(lines)
