# Frequently Asked Questions

## General

### What is Agentic Software Boutique?
An open platform for AI-assisted software development. It provides a web dashboard, multi-agent orchestration, MCP tool servers, and pluggable chat backends to interact with various AI coding agents.

### What AI backends are supported?
Claude Code (fully), OpenCode (fully), Codex (stub), Kimi (stub). The `ChatBackend` protocol makes it easy to add new backends.

### Do I need a subscription?
You need a Claude Code subscription to use the Claude backend. The dashboard and orchestration features work without any subscription.

### What is the "ponytail" philosophy?
A lazy-but-efficient development approach: use what already exists, prefer stdlib over dependencies, write the minimum code that works, and mark deliberate simplifications with `ponytail:` comments.

## Technical

### What database does it use?
SQLite with WAL mode, stored at `dashboard/data/chat.db`. No external database server required.

### Can I use PostgreSQL instead?
Not currently. The project is designed for single-user/small-team deployment where SQLite's simplicity wins. The persistence layer is isolated in `chat_store.py` for future replacement.

### How do I reset the database?
Delete `dashboard/data/chat.db` and restart the server. It will be recreated automatically.

### Is there a REST API?
Yes. All features are exposed via HTTP endpoints under `/api/`. See the [API Reference](../api/endpoints.md) for details.

### Can I run this in Docker?
The main application is not containerized — it runs directly with uvicorn. Docker is used only for sandbox agent isolation (see `sandbox/`).

## Development

### How do I add a new chat backend?
1. Create a new file in `dashboard/backends/`
2. Implement the `ChatBackend` ABC from `dashboard/backends/protocol.py`
3. Register it in `dashboard/backends/__init__.py`

### How do I add a new MCP server?
1. Create a new file in `dashboard/mcp/servers/`
2. Extend `MCPServer` from `dashboard/mcp/server.py`
3. Define tools with `ToolDef` and resources with `ResourceDef`
4. Register in `dashboard/main.py` during startup

### How do I add a new agent capability?
1. Add a new class extending `AgentCapability` in `dashboard/agents/protocol.py`
2. Create the implementation in `dashboard/agents/`
3. Register in `dashboard/agents/__init__.py`

## Operations

### How do I restart the service?
```bash
sudo systemctl restart agentic-software-boutique
```

### How do I view logs?
```bash
sudo journalctl -u agentic-software-boutique -f
```

### How often are backups taken?
Every 6 hours, with 7-day retention.

### How do I restore from backup?
```bash
bash dashboard/restore.sh
```

### Can I access the dashboard from outside the VPN?
By default, nginx restricts access to `10.0.0.0/24`. To change this, edit `dashboard/nginx.conf` and update the `allow` directives.
