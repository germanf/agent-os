# Windows Installation

## Prerequisites

1. Install **Python 3.11+** from [python.org](https://python.org)
2. Install **Node.js 20+** from [nodejs.org](https://nodejs.org)
3. Install **pnpm**: `npm install -g pnpm`
4. Install **Git** from [git-scm.com](https://git-scm.com)

## Clone and Setup

```powershell
git clone <repo-url>
cd agent-os

# Python virtual environment
python -m venv .venv
.venv\Scripts\activate
pip install --upgrade pip
pip install -r dashboard\requirements.txt

# Frontend dependencies
cd dashboard\frontend
pnpm install
cd ..\..
```

## Development Server

```powershell
# Terminal 1: backend
uvicorn dashboard.main:app --port 8765 --reload

# Terminal 2: frontend
cd dashboard\frontend
pnpm run dev
```

## Troubleshooting

- If `uvicorn` is not found, ensure your Python Scripts directory is in PATH
- On Windows, use `python` instead of `python3`
- For file path issues, use forward slashes or escaped backslashes

See [Quick Start](../getting-started/quickstart.md) for first-run instructions.
