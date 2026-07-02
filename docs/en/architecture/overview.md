# Architecture Overview

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│  nginx (port 80 → 443 redirect, 443 → proxy_pass :8765) │
│  VPN-only (allow 10.0.0.0/24), client_max_body_size 55M  │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│  uvicorn (port 8765) — FastAPI app                      │
│  dashboard/main.py                                      │
│                                                         │
│  Middleware stack:                                       │
│    AuthMiddleware (HTTP Basic Auth)                      │
│    HSTSHeaderMiddleware                                  │
│    TracingMiddleware (OpenTelemetry)                     │
│    RateLimiting (slowapi, per-endpoint)                  │
│                                                         │
│  Router modules:                                         │
│    agents, jobs, kanban, backends, notes,                │
│    projects, chats, diagnostics, alerts,                 │
│    orchestration, mcp, approvals, hermes_webhook,        │
│    cron, workflows, token_accounting                     │
│                                                         │
│  SPA catch-all: @app.get("/{full_path:path}")            │
└──┬───────────────┬──────────────┬───────────────────────┘
   │               │              │
   ▼               ▼              ▼
runner.py     chat_store.py   static files
(SSE jobs)    (SQLite DB)     (frontend/dist/)
```

## Module Responsibilities

### Dashboard Backend (`dashboard/`)

| Module | Responsibility |
|--------|---------------|
| `main.py` | FastAPI app entry point, middleware, routes, startup hooks, SPA fallback |
| `runner.py` | Generic async subprocess runner with SSE log streaming |
| `chat_store.py` | SQLite persistence for projects, chats, messages |
| `health.py` | Component-based health check registry |
| `alerts.py` | In-memory alert management system |
| `rate_limit.py` | slowapi rate limiter singleton |
| `tracing.py` | OpenTelemetry tracing middleware |
| `log.py` | Loguru logging with optional JSON serialization |
| `memory.py` | Project and org key-value memory stores (SQLite) |
| `token_accounting.py` | Token usage tracking |
| `backup.py` | Automated SQLite backup with rotation |
| `workflow.py` | Multi-step workflow definition and execution engine |

### Chat Backends (`dashboard/backends/`)

| Backend | Status | Description |
|---------|--------|-------------|
| `ClaudeBackend` | ✅ Complete | Claude Code (`claude -p` subprocess) |
| `OpencodeBackend` | ✅ Complete | OpenCode HTTP API + subprocess fallback |
| `CodexBackend` | ⚠️ Stub | GPT Codex backend (not implemented) |
| `KimiBackend` | ⚠️ Stub | Kimi Code backend (not implemented) |

### Orchestration (`dashboard/orchestrator/`)

| Module | Responsibility |
|--------|---------------|
| `task_graph.py` | TaskGraph DAG data model |
| `agent_pool.py` | Registered agent registry with health checks |
| `executor.py` | Async DAG executor with SSE streaming, retries, timeout |
| `aggregator.py` | Result collation from multiple subtasks |

### MCP System (`dashboard/mcp/`)

| Server | Tools | Resources |
|--------|-------|-----------|
| **memory** | `store/get/list/search` project/org memories | `memory://org/summary` |
| **notes** | `search_notes`, `read_note` | `notes://tree`, `notes://content/{path}` |
| **kanban** | `list/create/complete/show` tasks | — |
| **workflows** | `list/get/status` workflows | — |

### Agent System (`dashboard/agents/`)

| Agent | Capability | Description |
|-------|-----------|-------------|
| `HermesAgent` | OrchestratorCapability | Decomposes goals to kanban tasks, delegates |
| `OpencodeAgent` | DeveloperCapability | Bug fixes, features, refactoring via OpenCode |

## Layer Diagram

```
┌──────────────────────────────┐
│         Presentation         │
│   React SPA (Tailwind v4)    │
├──────────────────────────────┤
│           API Layer          │
│   FastAPI + uvicorn + SSE    │
├──────────────────────────────┤
│       Orchestration Layer    │
│   Task Graph → Agent Pool    │
├──────────────────────────────┤
│       Chat Backend Layer     │
│   Claude / OpenCode / etc.   │
├──────────────────────────────┤
│        Persistence Layer     │
│   SQLite (WAL mode)          │
└──────────────────────────────┘
```

## Execution Flow

1. User sends a chat message via the React UI
2. FastAPI routes the request to the appropriate chat backend
3. The backend spawns a subprocess (e.g., `claude -p`) or calls an HTTP API
4. Output is streamed back via SSE (Server-Sent Events)
5. Messages are persisted to SQLite via `chat_store.py`
6. For orchestration: tasks are decomposed into a DAG and executed via `executor.py`

## Architecture Decisions

See [Architecture Decision Records (ADRs)](../../adr/) for detailed rationale on specific decisions.

- **ADR-001**: In-process MCP servers (no wire protocol)
- **ADR-002**: SQLite over PostgreSQL (single-user, deployment simplicity)
- **ADR-003**: SSE over WebSocket (simplicity, HTTP compatibility)
- **ADR-004**: Agent-agnostic protocol (pluggable backends)
