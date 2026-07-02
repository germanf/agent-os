from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from dashboard.mcp.server import registry
from dashboard.rate_limit import limiter

router = APIRouter(prefix="/api/mcp", tags=["mcp"])


@router.get("/servers")
@limiter.limit("30/minute")
async def list_servers(request: Request):
    return JSONResponse([
        {
            "name": s.name,
            "version": s.version,
            "tool_count": len(await s.list_tools()),
            "resource_count": len(await s.list_resources()),
        }
        for s in registry.list()
    ])


@router.get("/tools")
@limiter.limit("30/minute")
async def list_all_tools(request: Request):
    tools = await registry.list_all_tools()
    return JSONResponse([
        {"server": s, "name": t.name, "description": t.description, "input_schema": t.input_schema}
        for s, t in tools
    ])


@router.get("/servers/{name}/tools")
@limiter.limit("30/minute")
async def list_server_tools(request: Request, name: str):
    server = registry.get(name)
    if not server:
        return JSONResponse({"error": "Server not found"}, status_code=404)
    tools = await server.list_tools()
    return JSONResponse([
        {"name": t.name, "description": t.description, "input_schema": t.input_schema}
        for t in tools
    ])


@router.get("/servers/{name}/resources")
@limiter.limit("30/minute")
async def list_server_resources(request: Request, name: str):
    server = registry.get(name)
    if not server:
        return JSONResponse({"error": "Server not found"}, status_code=404)
    resources = await server.list_resources()
    return JSONResponse([
        {"uri": r.uri, "name": r.name, "description": r.description, "mime_type": r.mime_type}
        for r in resources
    ])


@router.post("/servers/{name}/call")
@limiter.limit("30/minute")
async def call_tool(request: Request, name: str, body: dict):
    server = registry.get(name)
    if not server:
        return JSONResponse({"error": "Server not found"}, status_code=404)
    tool_name = body.get("tool", "")
    args = body.get("args", {})
    try:
        result = await server.call_tool(tool_name, args)
        return JSONResponse({"result": result})
    except ValueError as e:
        return JSONResponse({"error": str(e)}, status_code=400)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
