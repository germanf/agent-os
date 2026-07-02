
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
