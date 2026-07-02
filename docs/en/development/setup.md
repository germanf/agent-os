# Development Setup

## Repository Structure

```
agent-os/
├── AGENTS.md                  # Main dev conventions
├── README.md                  # Project overview
├── dashboard/                 # FastAPI backend + React SPA
│   ├── main.py                # App entry point
│   ├── chat_store.py          # SQLite persistence
│   ├── runner.py              # Async subprocess runner
│   ├── config.py              # Path constants
│   ├── health.py              # Health check registry
│   ├── alerts.py              # Alert system
│   ├── rate_limit.py          # Rate limiter
│   ├── tracing.py             # OpenTelemetry
│   ├── log.py                 # Logging config
│   ├── memory.py              # Key-value memory stores
│   ├── token_accounting.py    # Token tracking
│   ├── backup.py              # DB backup
│   ├── approvals.py           # Approval workflow
│   ├── checkpoints.py         # Job checkpoints
│   ├── kanban.py              # Kanban adapter
│   ├── kanban_feedback.py     # Kanban feedback poller
│   ├── workflow.py            # Workflow engine
│   ├── hermes_adapter.py      # Hermes CLI adapter
│   ├── headroom_sidecar.py    # Headroom proxy
│   ├── headroom_learn.py      # Headroom learning
│   ├── headroom_memory.py     # Headroom session memory
│   ├── cron_loop.py           # Cron ticker
│   ├── cron_adapter.py        # Hermes cron adapter
│   ├── curator_loop.py        # Curator review loop
│   ├── ponytail.py            # Ponytail plugin status
│   ├── start.sh               # Production deployment
│   ├── restore.sh             # DB restore
│   ├── diagnose.sh            # VM diagnostics
│   ├── nginx.conf             # Production nginx config
│   ├── .env.example           # Env vars template
│   ├── requirements.txt       # Python dependencies
│   ├── backends/              # Chat backend implementations
│   │   ├── protocol.py        # ABC + normalized events
│   │   ├── claude.py          # Claude Code backend
│   │   ├── opencode.py        # OpenCode backend
│   │   ├── codex.py           # Codex backend (stub)
│   │   └── kimi.py            # Kimi backend (stub)
│   ├── agents/                # Agent capability implementations
│   │   ├── protocol.py        # ABCs: Developer, Reviewer, QA, Orchestrator
│   │   ├── hermes_agent.py    # Hermes orchestrator
│   │   └── opencode_agent.py  # OpenCode developer
│   ├── orchestrator/          # Multi-agent orchestration
│   │   ├── task_graph.py      # DAG data model
│   │   ├── agent_pool.py      # Agent registry
│   │   ├── executor.py        # Async DAG executor
│   │   └── aggregator.py      # Result collation
│   ├── mcp/                   # MCP tool server system
│   │   ├── server.py          # ABC + registry
│   │   ├── client.py          # Discovery helpers
│   │   └── servers/           # MCP server implementations
│   │       ├── memory.py      # Memory server
│   │       ├── notes.py       # Notes server
│   │       ├── kanban.py      # Kanban server
│   │       └── workflows.py   # Workflows server
│   ├── middleware/             # ASGI middleware
│   │   ├── auth.py            # HTTP Basic Auth
│   │   └── hsts.py            # HSTS headers
│   ├── routes/                # API route handlers
│   │   ├── agents.py          # /api/agents
│   │   ├── alerts.py          # /api/alerts
│   │   ├── approvals.py       # /api/approvals
│   │   ├── backends.py        # /api/backends
│   │   ├── chats.py           # /api/chats, /api/chat
│   │   ├── cron.py            # /api/cron
│   │   ├── diagnostics.py     # /api/diagnostics, /api/health
│   │   ├── hermes_webhook.py  # /api/hermes/webhook
│   │   ├── jobs.py            # /api/jobs
│   │   ├── kanban.py          # /api/kanban
│   │   ├── mcp.py             # /api/mcp
│   │   ├── notes.py           # /api/notes
│   │   ├── orchestrator.py    # /api/orchestrator
│   │   ├── projects.py        # /api/projects
│   │   ├── token_accounting.py# /api/tokens
│   │   └── workflows.py       # /api/workflows
│   ├── models/                # Pydantic schemas
│   │   └── schemas.py
│   ├── skills/                # Hermes skill definitions
│   └── data/                  # SQLite databases + uploads (gitignored)
├── frontend/                  # (actually dashboard/frontend/)
│   └── src/
│       ├── App.tsx            # Routes
│       ├── main.tsx           # Entry point
│       ├── index.css          # Tailwind v4 config
│       ├── pages/             # Page components
│       ├── components/        # Shared UI components
│       └── lib/               # Utilities, hooks, tests
├── sandbox/                   # Docker sandbox for agents
├── specs/                     # Role definitions + workflow
├── tests/                     # Python test scripts
├── docs/                      # Documentation
│   ├── en/                    # English docs
│   ├── es/                    # Spanish docs
│   ├── adr/                   # Architecture Decision Records
│   └── assets/                # Images and diagrams
├── scripts/                   # Utility scripts
└── tmp/                       # Temporary files (gitignored)
```

## Coding Standards

### Python
- **Style**: ruff (configured in `pyproject.toml`)
- **Type hints**: required for all function signatures
- **Syntax check**: `python3 -m py_compile dashboard/main.py`
- **Lint**: `ruff check dashboard/`
- **Format**: ruff formatter

### TypeScript / React
- **TypeScript**: strict mode, `tsc -b` for type checking
- **Lint**: ESLint (flat config in `eslint.config.js`)
- **Build**: `pnpm run build` (runs `tsc -b && vite build`)
- **Framework**: React 19 with functional components and hooks
- **Styling**: Tailwind v4 CSS-first config via `@theme` in `index.css`

### General
- No CI/CD in repo — deployment is manual via `dashboard/start.sh`
- Every issue gets exactly one label: `bug`, `feature`, `security`, or `documentation`
- Temporary files go in `tmp/` (project root) — never `/tmp/` or system temp

## Development Workflow

See `specs/workflow.md` for the full pipeline:
```
Issue → Plan → Dev → CTO Review → Human Approval → CTO Merge → QA → Close
```

### Quick Commands

```bash
# Backend
uvicorn dashboard.main:app --port 8765 --reload
ruff check dashboard/
python3 -m py_compile dashboard/main.py

# Frontend
cd dashboard/frontend
pnpm run dev         # Dev server (proxies to :8765)
pnpm run build       # TypeScript check + production build
pnpm run test        # Vitest
pnpm run lint        # ESLint
```

## Debugging

- For backend issues: check FastAPI logs in the terminal running uvicorn
- For frontend issues: browser DevTools (Console, Network tabs)
- SSE streams can be inspected at `/api/jobs/{id}/stream` or `/api/orchestrator/tasks/{id}/stream`
- Database inspection: `sqlite3 dashboard/data/chat.db` (WAL mode)
