# System Architecture

## Overview

Monorepo with two Twitter data exporters, a FastAPI dashboard backend, and a React SPA frontend.

```
┌─────────────────────────────────────────────────────────┐
│  nginx (port 80 → 443 redirect, 443 → proxy_pass :8765) │
│  VPN-only (allow 10.0.0.0/24), client_max_body_size 55M  │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│  uvicorn (port 8765) — FastAPI app                      │
│  dashboard/main.py:941 lines                            │
│                                                         │
│  AuthMiddleware (Basic HTTP, DASH_USER/DASH_PASS env)   │
│  @limiter.limit("N/minute") on every endpoint           │
│  SPA catch-all @app.get("/{full_path:path}") at line 936│
└──┬───────────────┬──────────────┬───────────────────────┘
   │               │              │
   ▼               ▼              ▼
runner.py     chat_store.py   static files
(SSE jobs)    (SQLite DB)     (frontend/dist/)
```

## Packages

| Directory | Entrypoint | Role |
|-----------|-----------|------|
| `dashboard/` | `main.py` | FastAPI backend + serves React SPA |
| `dashboard/frontend/` | `src/main.tsx` → `App.tsx` | React SPA (Vite build → `dist/`) |
| `~~twitter-exporters/~~ (removed)` | `main.py` | X API v2 exporter (tweepy, OAuth PKCE) |
| `~~agentic-twitter-claude/~~ (removed)` | `main.py` | Playwright scraper (browser login, GraphQL) |
| `sandbox/` | `Dockerfile.base` | Docker sandbox for parallel agents |

## Backend flow

1. **Jobs**: Clients `POST /api/run/*` → `runner.create_job()` → `BackgroundTasks` → `runner.run_job()` (async subprocess) → SSE streaming via `GET /api/jobs/{id}/stream`
2. **Chat**: `POST /api/chat/send` → spawns `claude -p` subprocess per message → `runner.py` for streaming → response parsed and persisted in SQLite
3. **Auth**: `AuthMiddleware` checks HTTP Basic Auth on every request except `/api/health` and `/auth/callback`
4. **SPA**: All unmatched routes (`/{full_path:path}`) serve `frontend/dist/index.html` — must be defined *last* in main.py

## Frontend routes

| Path | Component | Data source |
|------|-----------|-------------|
| `/` | Landing | Static nav cards |
| `~~/scrapers~~ (removed)` | Scrapers | `POST /api/run/*` + SSE stream |
| `/resumen` | Resumen | `GET /api/resumen` (from `outputs/manual/organized/resumen.json`) |
| `/notes` | Notes | `GET /api/notes/tree`, `GET /api/notes/content` (Obsidian vault) |
| `/chat` | Chat | `GET /api/chats` (list), `POST /api/chat/send` |
| `/chat/:chatId` | Chat | `GET /api/chats/{id}`, SSE stream |

## Production VM resources (not in sandbox)

- `claude` CLI subscription — required by `/chat`
- `/home/ubuntu/vault/` — Obsidian vault for `/notes`
- nginx + uvicorn on ports 80/443/8765
- iptables firewall — new `listen <port>` in nginx.conf also needs iptables rule
