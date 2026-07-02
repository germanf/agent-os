# API Reference

**Base URL:** `http://127.0.0.1:8765` (dev) / `https://10.0.0.227` (production)

**Auth:** HTTP Basic Auth (`DASH_USER`/`DASH_PASS` env vars). Exception: `/api/health`.

**Rate limit:** `slowapi` — `@limiter.limit("N/minute")` on every endpoint.

## Public (no auth)

| Method | Path | Rate | Description |
|--------|------|------|-------------|
| GET | `/api/health` | 60/min | Health check → `{"status":"ok","timestamp":...}` |

## Jobs

| Method | Path | Rate | Description |
|--------|------|------|-------------|
| GET | `/api/jobs` | 30/min | List all jobs |
| GET | `/api/jobs/{id}` | 30/min | Get job status |
| GET | `/api/jobs/{id}/logs` | 30/min | Get job logs |
| GET | `/api/jobs/{id}/stream` | 30/min | SSE log stream |
| POST | `/api/jobs/{id}/cancel` | 30/min | Cancel running job |

## Notes (Obsidian vault)

| Method | Path | Rate | Description |
|--------|------|------|-------------|
| GET | `/api/notes/tree` | 30/min | File tree of vault (`[]` if vault absent) |
| GET | `/api/notes/content?path=` | 30/min | Read note content (path-traversal validated) |

## Chat

| Method | Path | Rate | Description |
|--------|------|------|-------------|
| GET | `/api/projects` | 30/min | List projects |
| POST | `/api/projects` | 30/min | Create project |
| PATCH | `/api/projects/{id}` | 30/min | Update project name/prompt |
| DELETE | `/api/projects/{id}` | 30/min | Delete project |
| POST | `/api/projects/{id}/folders` | 30/min | Add folder to project |
| DELETE | `/api/projects/folders/{id}` | 30/min | Remove folder |
| GET | `/api/chats` | 30/min | List chats (`?project_id=` optional) |
| POST | `/api/chats` | 30/min | Create chat (body: `{id?, project_id?}`) |
| GET | `/api/chats/{id}` | 30/min | Get chat with messages |
| PATCH | `/api/chats/{id}` | 30/min | Rename chat |
| DELETE | `/api/chats/{id}` | 30/min | Delete chat |
| POST | `/api/chat/send` | 10/min | Send message → spawn `claude -p` subprocess |
| POST | `/api/files/upload` | 3/min | Upload files for chat (max 10 files, 10 MB/file, 50 MB total) |

## Diagnostics

| Method | Path | Rate | Description |
|--------|------|------|-------------|
| GET | `/api/diagnostics` | 30/min | Deployment health details |
