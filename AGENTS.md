# Agentic Software Boutique

Stack: **Python 3.11+ FastAPI + uvicorn** (backend), **Vite + React 19 + TypeScript + Tailwind v4** (frontend in `dashboard/frontend/`).  
Build served by FastAPI from `dashboard/frontend/dist/` via catch-all SPA handler (`main.py:560`).

## Development workflow

See `specs/workflow.md` for the full pipeline and `specs/workflow.yaml` for the machine-readable definition.

```
Issue → Plan (CTO) → Dev (branch + PR)
→ Tech Lead Code Review (mandatory gate)
→ CTO approves → CTO merges to dev
→ QA → [Pass → CTO PR to main | Fail → loop]
→ Close
```

## Workflow Protocol (Non-negotiable)

The development pipeline is defined in **machine-readable YAML** (`specs/workflow.yaml`) with a JSON Schema (`specs/workflow.schema.json`). Every agent MUST:

1. Load `specs/workflow.yaml` at session start
2. Follow the defined stages in order
3. Verify preconditions before proceeding to a stage
4. Verify postconditions before marking a stage complete
5. Use the defined handoff protocol (`specs/protocol.md`) for agent-to-agent communication
6. Run `bash scripts/validate-workflow.sh` before pushing any code

Enforcement mechanisms:
- **Pre-push hook** (`.githooks/pre-push`): runs validation on every push. Install: `git config core.hooksPath .githooks`
- **PR template** (`.github/PULL_REQUEST_TEMPLATE.md`): mandatory checklist in every PR

## Agent roles

| Role | File | Scope | Gate |
|------|------|-------|------|
| CTO | `specs/roles/cto.md` | Architecture, launch agents, verify workflows, approve PRs, sole PR-to-main authority | Mandatory |
| Tech Lead | `specs/roles/tech-lead.md` | Automated Code Review (mandatory gate), Security/UI-UX triage, delegation to Dev | Mandatory |
| Full Stack Developer | `specs/roles/fullstack-developer.md` | Feature/bug implementation | Mandatory |
| QA/Tester | `specs/roles/qa-tester.md` | Validation against test plan, QA loop with escalation | Mandatory |
| Security Specialist | `specs/roles/security-specialist.md` | Pentesting, black box, SAST/DAST → creates Issue | On demand |
| UI/UX Specialist | `specs/roles/ui-ux-specialist.md` | Design/UX review, accessibility audit → creates Issue | On demand |
| Advisory | — (see CTO) | Deep architecture review on CTO request (loop exhaustion, complex design) | On demand (CTO-activated) |

### Hierarchy

```
CTO ── launches agents, verifies workflows, approves PRs, sole PR-to-main authority
 ├── Tech Lead ── Code Review (gate), Security/UI-UX triage, delegate to Dev
 ├── Full Stack Developer ── implementation
 ├── QA/Tester ── validation, QA loop
 ├── Security Specialist ── pentesting → Issue
 └── UI/UX Specialist ── design/UX review → Issue
      ↑
 Advisory ── deep review on CTO request
```

## Sandbox isolation

See `specs/sandbox.md` for conventions.
See `sandbox/README.md` for implementation details.

## Quick commands

```bash
# Backend
uvicorn dashboard.main:app --port 8765 --reload          # dev server
python3 -m py_compile dashboard/main.py                   # syntax check
ruff check dashboard/                                      # lint (install: pip install ruff)

# Frontend (dashboard/frontend/)
pnpm run dev           # Vite dev server, proxies /api and /auth to :8765
pnpm run build         # tsc -b + vite build → dist/
pnpm run test          # vitest
pnpm run test:coverage # vitest --coverage
pnpm run lint          # eslint

# Deployment (production VM)
bash dashboard/start.sh   # idempotent: builds frontend, creates venv, configures nginx+systemd
```

## Architecture

- `dashboard/main.py` — FastAPI app. **All API/auth routes before** the catch-all at line 560 (`@app.get("/{full_path:path}")`). Never add routes after it.
- `dashboard/runner.py` — generic async subprocess runner (`create_job(tool, command, cwd)` + SSE streaming). `tool` is a free string, add new tools without modifying this file.
- `dashboard/chat_store.py` — SQLite persistence for `/chat` (projects, chats, messages). DB at `dashboard/data/chat.db`, WAL mode, auto-created on startup `@app.on_event("startup")`.
- `dashboard/nginx.conf` — reverse proxy, HTTP→HTTPS redirect, VPN-only (`allow 10.0.0.0/24; deny all;`), SSE buffering off, client_max_body_size 55M (uploads).
- `dashboard/start.sh` — production deploy: builds frontend, replaces venv atomically, generates self-signed TLS cert, installs nginx config + systemd service.

### Multi-package structure

| Directory | Purpose |
|-----------|---------|
| `dashboard/` | FastAPI backend + React SPA |
| `sandbox/` | Docker sandbox infrastructure for parallel agents |
| `specs/` | Agent role definitions and development workflow |
| `tests/` | Rate-limit / edge-case tests (Python scripts, not a formal suite) |
| `docs/` | Architecture, API, DB schema, ops documentation |

### Frontend routes (React SPA, `App.tsx`)

`/` → Landing, `/notes` → Notes, `/chat` → Chat, `/chat/:chatId` → Chat

### Key API endpoints (all behind HTTP Basic Auth except `/api/health`)

- `GET /api/jobs` / `GET /api/jobs/{job_id}` — list and inspect jobs (via runner.py)
- `GET /api/jobs/{job_id}/stream` — SSE log streaming
- `GET /api/jobs/{job_id}/logs` — past job logs
- `POST /api/jobs/{job_id}/cancel` — cancel a running job
- `GET /api/notes/tree` / `GET /api/notes/content` — Obsidian vault browsing (production only; returns `[]` gracefully when vault missing)
- `GET /api/projects` / `POST /api/projects` / `PATCH /api/projects/{id}` / `DELETE /api/projects/{id}` — project CRUD
- `POST /api/projects/{id}/folders` / `DELETE /api/projects/folders/{id}` — project folder management
- `GET /api/chats` / `POST /api/chats` / `GET /api/chats/{id}` / `PATCH /api/chats/{id}` / `DELETE /api/chats/{id}` — chat CRUD
- `POST /api/chat/send` — spawns `claude -p` subprocess per message (production only; uses `--resume` for continuity)
- `POST /api/files/upload` — file upload for chat (validated: 10 MB/file, 50 MB total, 10 files)
- `GET /api/health` — health check (no auth required)
- `GET /api/diagnostics` — deployment health details (frontend built, DB exists, vault exists, Python/FastAPI/uvicorn versions)

## Conventions

- **Temporary files**: ALWAYS use `tmp/` (project root) — **never** `/tmp/`, `/dev/shm/`, or any system temp. This is **non-negotiable**: system temp dirs are outside the project, invisible to git, don't get cleaned up by project scripts, and create reproducibility issues. `tmp/` is gitignored, project-scoped, and cleaned by `git clean`. If you used `/tmp/` for anything, it's a bug — move it.

- **Tailwind v4**: CSS-first config via `@theme` in `index.css` (no `tailwind.config.ts`). Dark theme: `--color-bg: #0d1117`, `--color-surface: #161b22`, `--color-accent: #7C3AED`.
- **Secrets**: `dashboard/.credentials.json` and `.env` files (all gitignored, chmod 0600). Never hardcode, log, or commit real credentials.
- **Secrets masking**: API secrets sent back from `/api/credentials` are masked as `••••••••`; the POST endpoint preserves existing values when masked is submitted.
- **HTTP Basic Auth** in middleware (`AuthMiddleware` class) vs nginx: enforced at the app layer from `DASH_USER`/`DASH_PASS` env vars. Exceptions: `/api/health`.
- **Rate limiting**: `slowapi` middleware — `@limiter.limit("N/minute")` on every API endpoint.
- **Job retention**: finished jobs evicted after 1 hour, max 200 finished jobs in memory.
- **Frontend testing**: vitest + @testing-library/react in `dashboard/frontend/`.
- **No CI/CD in repo**: no `.github/` directory. Deployment is manual via `dashboard/start.sh` on the production VM, triggered by a self-hosted GitHub Actions runner (configured outside this repo on the VM).
- **GitHub issue labels** (team convention, enforced via `specs/workflow.md`): every issue gets exactly one of `bug`, `feature`, `security`, `documentation`.

## Production VM (resources absent from this sandbox)

- `claude` CLI (authenticated subscription) — needed by `/chat`
- `/home/ubuntu/vault/` — Obsidian vault, needed by `/notes`
- `nginx` + `uvicorn` on ports 80/443/8765
- iptables firewall (persisted via `netfilter-persistent`): adding a new `listen <port>` in nginx.conf also needs a matching iptables rule before the traffic flows.

**Static verification in sandbox**: `python3 -m py_compile`, `pnpm run build`, instantiate FastAPI app and check `app.routes`, test API endpoints with `TestClient`. Never try to simulate Claude CLI, vault, or nginx here.

## Sandbox containers (`sandbox/`)

Role-based port ranges (fullstack: 8800-8849, QA: 8850-8899, UI: 8900-8949).  
Critical cleanup order: stop container FIRST (`sandbox-down.sh`), then remove worktree.  
See `sandbox/README.md` and `sandbox/VALIDATION.md`.
