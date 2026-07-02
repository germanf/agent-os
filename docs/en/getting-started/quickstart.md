# Quick Start

## Prerequisites

- Python 3.11+
- Node.js 20+
- pnpm
- Git

## Installation

```bash
git clone <repo-url>
cd agent-os

# Backend
cd dashboard
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Frontend
cd frontend
pnpm install
```

## First Run

```bash
# Start the backend dev server (from dashboard/)
uvicorn dashboard.main:app --port 8765 --reload

# In another terminal, start the frontend dev server (from dashboard/frontend/)
pnpm run dev
```

Open `http://localhost:5173` in your browser. The Vite dev server proxies `/api` and `/auth` requests to the FastAPI backend on port 8765.

## Basic Workflow

1. **Set up authentication** — configure `DASH_USER` and `DASH_PASS` environment variables, or create a `dashboard/.credentials.json` file
2. **Explore the dashboard** — navigate to `/` for the landing page, `/dashboard` for system status
3. **Start a chat** — go to `/chat` to open a conversation with an AI backend
4. **Create a task graph** — go to `/orchestrator` to define multi-agent workflows
5. **Browse notes** — if an Obsidian vault is configured, visit `/notes`

## What's Next?

- [Installation Guide](../installation/linux.md)
- [Configuration Reference](../configuration/environment.md)
- [Architecture Overview](../architecture/overview.md)
