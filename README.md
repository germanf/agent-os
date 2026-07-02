# Agentic Software Boutique

> **🇺🇸 English** · [🇪🇸 Español](docs/es/README.md)

A generic, domain-agnostic platform for AI-assisted software development. Provides a web dashboard, multi-agent orchestration, MCP tool ecosystem, and pluggable AI backends — wire it to your own project, codebase, and infrastructure.

**The best code is the code never written.**

## Features

- **Multi-Agent Orchestration** — DAG-based task graphs with parallel/sequential execution, SSE streaming, and agent load balancing
- **MCP Ecosystem** — 4 in-process tool servers (Memory, Notes, Kanban, Workflows) with registry and admin UI
- **Pluggable Backends** — Claude Code, OpenCode, Codex, Kimi via `ChatBackend` protocol
- **Web Dashboard** — React SPA with health monitoring, job management, chat interface, vault browsing
- **Kanban Workflow** — Task tracking with approvals, cron scheduling, and feedback polling
- **Observability** — Health checks, structured logging (JSON), alerts, OpenTelemetry tracing
- **Production Hardening** — Rate limiting, HTTP Basic Auth, HSTS, SQLite WAL backups (6h/7day retention)
- **Sandbox Isolation** — Docker containers for parallel agent execution with per-role port ranges
- **Ponytail Mode** — Lazy-development philosophy: stdlib first, minimal working solutions, no over-engineering

## Requirements

- Python 3.11+
- Node.js 20+
- pnpm
- Optional: Claude Code, Hermes, Headroom CLIs

## Quick Start

```bash
git clone <repo-url>
cd agent-os

# Backend
cd dashboard
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn dashboard.main:app --port 8765 --reload &

# Frontend (separate terminal)
cd dashboard/frontend
pnpm install
pnpm run dev
```

Open `http://localhost:5173`. Set `DASH_USER` and `DASH_PASS` for auth.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│  nginx (port 80 → 443 redirect, 443 → proxy_pass :8765) │
│  VPN-only (allow 10.0.0.0/24), client_max_body_size 55M  │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│  uvicorn (port 8765) — FastAPI app                      │
│  AuthMiddleware · HSTS · Tracing · RateLimiting          │
│  Routes: agents, jobs, chat, orchestrator, mcp, ...     │
│  SPA catch-all @app.get("/{full_path:path}")             │
└──┬───────────────┬──────────────┬───────────────────────┘
   │               │              │
   ▼               ▼              ▼
runner.py     chat_store.py   static files
(SSE jobs)    (SQLite DB)     (frontend/dist/)
```

### Key Modules

| Directory | Purpose |
|-----------|---------|
| `dashboard/` | FastAPI backend + React SPA |
| `dashboard/backends/` | Pluggable chat backends (Claude, OpenCode, Codex, Kimi) |
| `dashboard/agents/` | Agent capability implementations |
| `dashboard/orchestrator/` | Multi-agent DAG task execution |
| `dashboard/mcp/` | MCP tool/resource server system |
| `sandbox/` | Docker-based agent isolation |
| `specs/` | Role definitions and development workflow |
| `docs/` | Bilingual documentation (EN/ES) |

## Documentation

Full documentation is available in [`docs/`](docs/README.md):

| Section | English | Español |
|---------|---------|---------|
| Getting Started | [EN](docs/en/getting-started/overview.md) | [ES](docs/es/getting-started/overview.md) |
| Installation | [EN](docs/en/installation/linux.md) | [ES](docs/es/installation/linux.md) |
| Configuration | [EN](docs/en/configuration/environment.md) | [ES](docs/es/configuration/environment.md) |
| Architecture | [EN](docs/en/architecture/overview.md) | [ES](docs/es/architecture/overview.md) |
| API Reference | [EN](docs/en/api/endpoints.md) | [ES](docs/es/api/endpoints.md) |
| Deployment | [EN](docs/en/deployment/production.md) | [ES](docs/es/deployment/production.md) |
| Contributing | [EN](docs/en/contributing/guidelines.md) | [ES](docs/es/contributing/guidelines.md) |

## Examples

```bash
# Check system health
curl http://127.0.0.1:8765/api/health

# Create a task graph (requires auth)
curl -u user:pass -X POST http://127.0.0.1:8765/api/orchestrator/tasks \
  -H "Content-Type: application/json" \
  -d '{"subtasks": [{"id":"s1","description":"Analyze codebase"}]}'

# List available agents
curl -u user:pass http://127.0.0.1:8765/api/orchestrator/agents

# List MCP servers
curl -u user:pass http://127.0.0.1:8765/api/mcp/servers
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) and [specs/workflow.md](specs/workflow.md).

## License

MIT
