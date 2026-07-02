# Linux Installation

## Prerequisites

```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv nodejs npm git curl
sudo npm install -g pnpm
```

## Clone and Setup

```bash
git clone <repo-url>
cd agent-os

# Python virtual environment
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r dashboard/requirements.txt

# Frontend dependencies
cd dashboard/frontend
pnpm install
cd ../..
```

## Development Server

```bash
# Terminal 1: backend
uvicorn dashboard.main:app --port 8765 --reload

# Terminal 2: frontend
cd dashboard/frontend && pnpm run dev
```

See [Quick Start](../getting-started/quickstart.md) for first-run instructions.
