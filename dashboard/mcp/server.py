from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from loguru import logger


@dataclass
class ToolDef:
    name: str
    description: str
    input_schema: dict


@dataclass
class ResourceDef:
    uri: str
    name: str
    description: str
    mime_type: str = "text/plain"


class MCPServer(ABC):
    name: str = ""
    version: str = "1.0.0"

    @abstractmethod
    async def list_tools(self) -> list[ToolDef]: ...

    @abstractmethod
    async def call_tool(self, name: str, args: dict) -> Any: ...

    async def list_resources(self) -> list[ResourceDef]:
        return []

    async def read_resource(self, uri: str) -> str:
        raise NotImplementedError(f"read_resource not implemented for {uri}")


class MCPServerRegistry:
    def __init__(self):
        self._servers: dict[str, MCPServer] = {}

    def register(self, server: MCPServer):
        self._servers[server.name] = server
        logger.info("MCP server registered: {} v{}", server.name, server.version)

    def deregister(self, name: str):
        self._servers.pop(name, None)

    def get(self, name: str) -> MCPServer | None:
        return self._servers.get(name)

    def list(self) -> list[MCPServer]:
        return list(self._servers.values())

    async def list_all_tools(self) -> list[tuple[str, ToolDef]]:
        result = []
        for server in self._servers.values():
            for tool in await server.list_tools():
                result.append((server.name, tool))
        return result

    async def list_all_resources(self) -> list[tuple[str, ResourceDef]]:
        result = []
        for server in self._servers.values():
            for resource in await server.list_resources():
                result.append((server.name, resource))
        return result

    async def call_tool(self, server_name: str, tool_name: str, args: dict) -> Any:
        server = self._servers.get(server_name)
        if not server:
            raise ValueError(f"MCP server not found: {server_name}")
        return await server.call_tool(tool_name, args)


registry = MCPServerRegistry()
