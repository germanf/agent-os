---
name: agent-os-platform
description: Agent OS platform — architecture, backends, and API conventions
version: 1.0.0
author: agent-os
metadata:
  hermes:
    tags: [platform, architecture, agent-os]
    requires_toolsets: [terminal, web]
---

## Description

Agent OS is a self-improving development platform. It provides a FastAPI backend with multiple agentic backends (Claude, OpenCode, Codex, Kimi), SQLite persistence for memory and tokens, and a React SPA frontend.

## Architecture

- **Backend**: FastAPI + uvicorn, single process
- **Frontend**: React + TypeScript + Tailwind v4 SPA (in `dashboard/frontend/`)
- **Database**: SQLite via aiosqlite, WAL mode
- **Auth**: HTTP Basic Auth (exceptions: `/api/health`)
- **Rate limiting**: slowapi, applied to every endpoint

All API routes except `/api/health` require authentication.

## Key API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | /api/health | Health check (no auth) |
| GET | /api/jobs | List jobs |
| POST | /api/projects | Create project |
| GET | /api/projects | List projects |
| POST | /api/chat/send | Send message to agent |

## Agent Backends

The system supports multiple backends via `ChatBackend` ABC:
- `ClaudeBackend` — Claude Code CLI (`claude -p`)
- `OpencodeBackend` — OpenCode CLI (`opencode run`)
- `CodexBackend` — GPT Codex (stub)
- `KimiBackend` — Kimi (stub)

Select backend via `AGENT_BACKEND` env var.

## Skill Installation

Skills are installed in `~/.hermes/skills/`. Use `/reload-skills` after installing new skills.

## Verification

Load this skill with `/skill agent-os-platform` and ask the agent about the architecture.
