# API Reference

**Base URL:** `http://127.0.0.1:8765` (development) / `https://your-domain` (production)

**Authentication:** HTTP Basic Auth via `DASH_USER`/`DASH_PASS`.
**Exception:** `/api/health` is public.

**Rate Limiting:** Every endpoint has a slowapi limit (typically 30/min).
**Response Format:** JSON unless otherwise noted. SSE endpoints return `text/event-stream`.

## Public Endpoints

| Method | Path | Rate | Description |
|--------|------|------|-------------|
| GET | `/api/health` | 60/min | Health check |

## Jobs

| Method | Path | Rate | Description |
|--------|------|------|-------------|
| GET | `/api/jobs` | 30/min | List all jobs |
| GET | `/api/jobs/{id}` | 30/min | Get job details |
| GET | `/api/jobs/{id}/stream` | 30/min | SSE log stream |
| GET | `/api/jobs/{id}/events` | 30/min | SSE parsed event stream |
| GET | `/api/jobs/{id}/logs` | 30/min | Past job logs |
| POST | `/api/jobs/{id}/cancel` | 30/min | Cancel running job |
| POST | `/api/jobs/{id}/checkpoint` | 30/min | Save checkpoint |
| GET | `/api/jobs/checkpoints` | 30/min | List checkpoints |
| GET | `/api/jobs/orphans` | 30/min | Orphaned checkpoints |
| POST | `/api/jobs/checkpoints/{id}/resume` | 30/min | Resume from checkpoint |

## Chat System

| Method | Path | Rate | Description |
|--------|------|------|-------------|
| GET | `/api/projects` | 30/min | List projects |
| POST | `/api/projects` | 10/min | Create project |
| PATCH | `/api/projects/{id}` | 10/min | Update project |
| DELETE | `/api/projects/{id}` | 10/min | Delete project |
| POST | `/api/projects/{id}/folders` | 10/min | Add folder to project |
| DELETE | `/api/projects/folders/{id}` | 10/min | Remove folder |
| GET | `/api/chats` | 30/min | List chats |
| POST | `/api/chats` | 10/min | Create chat |
| GET | `/api/chats/{id}` | 30/min | Get chat |
| PATCH | `/api/chats/{id}` | 10/min | Update chat |
| DELETE | `/api/chats/{id}` | 10/min | Delete chat |
| GET | `/api/chats/{id}/messages` | 30/min | Get messages |
| POST | `/api/chat/send` | 10/min | Send message (returns SSE) |
| POST | `/api/files/upload` | 10/min | Upload file for chat |

## Notes (Obsidian Vault)

| Method | Path | Rate | Description |
|--------|------|------|-------------|
| GET | `/api/notes/tree` | 30/min | Vault file tree |
| GET | `/api/notes/content?path=` | 30/min | Read note content |

## Orchestrator

| Method | Path | Rate | Description |
|--------|------|------|-------------|
| POST | `/api/orchestrator/tasks` | 10/min | Create task graph |
| GET | `/api/orchestrator/tasks` | 30/min | List graphs |
| GET | `/api/orchestrator/tasks/{id}` | 30/min | Get graph details |
| DELETE | `/api/orchestrator/tasks/{id}` | 10/min | Cancel graph |
| GET | `/api/orchestrator/tasks/{id}/stream` | 30/min | SSE task events |
| GET | `/api/orchestrator/agents` | 30/min | List available agents |

## MCP

| Method | Path | Rate | Description |
|--------|------|------|-------------|
| GET | `/api/mcp/servers` | 30/min | List MCP servers |
| GET | `/api/mcp/tools` | 30/min | All tools across servers |
| GET | `/api/mcp/servers/{name}/tools` | 30/min | Server-specific tools |
| GET | `/api/mcp/servers/{name}/resources` | 30/min | Server-specific resources |
| POST | `/api/mcp/servers/{name}/call` | 10/min | Invoke a tool |

## Kanban

| Method | Path | Rate | Description |
|--------|------|------|-------------|
| GET | `/api/kanban/tasks` | 30/min | List kanban tasks |
| POST | `/api/kanban/tasks` | 10/min | Create task |
| GET | `/api/kanban/tasks/{id}` | 30/min | Get task details |
| POST | `/api/kanban/tasks/{id}/complete` | 10/min | Complete task |
| POST | `/api/kanban/tasks/{id}/block` | 10/min | Block task |
| POST | `/api/kanban/tasks/{id}/unblock` | 10/min | Unblock task |
| POST | `/api/kanban/feedback/poll` | 30/min | Poll feedback |

## Approvals

| Method | Path | Rate | Description |
|--------|------|------|-------------|
| GET | `/api/approvals/pending` | 30/min | Pending approvals |
| POST | `/api/approvals/{id}/approve` | 10/min | Approve |
| POST | `/api/approvals/{id}/deny` | 10/min | Deny |
| POST | `/api/approvals/{id}/complete-task` | 10/min | Complete after approval |

## Diagnostics

| Method | Path | Rate | Description |
|--------|------|------|-------------|
| GET | `/api/diagnostics` | 10/min | Full deployment diagnostics |
| GET | `/api/ponytail/metrics` | 30/min | Ponytail metrics |

## Alerts

| Method | Path | Rate | Description |
|--------|------|------|-------------|
| GET | `/api/alerts` | 30/min | List alerts |
| POST | `/api/alerts/{id}/acknowledge` | 10/min | Acknowledge alert |
| POST | `/api/alerts/acknowledge-all` | 10/min | Acknowledge all |

## Token Accounting

| Method | Path | Rate | Description |
|--------|------|------|-------------|
| GET | `/api/tokens` | 30/min | Token log entries |
| POST | `/api/tokens` | 10/min | Log token usage |
| GET | `/api/tokens/summary` | 30/min | Token usage summary |

## Workflows

| Method | Path | Rate | Description |
|--------|------|------|-------------|
| GET | `/api/workflows` | 30/min | List workflow defs |
| POST | `/api/workflows/load` | 10/min | Load workflow from file |
| GET | `/api/workflows/{name}` | 30/min | Get workflow details |
| POST | `/api/workflows/{name}/execute` | 10/min | Execute workflow |
| GET | `/api/workflows/{name}/status` | 30/min | Workflow status |

## Background Jobs (Cron)

| Method | Path | Rate | Description |
|--------|------|------|-------------|
| GET | `/api/cron/jobs` | 30/min | List cron jobs |
| POST | `/api/cron/jobs` | 10/min | Create cron job |
| POST | `/api/cron/jobs/{name}/pause` | 10/min | Pause job |
| POST | `/api/cron/jobs/{name}/resume` | 10/min | Resume job |
| POST | `/api/cron/jobs/{name}/run-now` | 10/min | Run immediately |
| DELETE | `/api/cron/jobs/{name}` | 10/min | Delete job |
| POST | `/api/cron/tick` | 30/min | Trigger cron tick |
| GET | `/api/cron/status` | 30/min | Cron system status |

## Other

| Method | Path | Rate | Description |
|--------|------|------|-------------|
| GET | `/api/backends` | 30/min | List available chat backends |
| GET | `/api/agents` | 30/min | List registered agents |
| POST | `/api/hermes/webhook` | 30/min | Hermes kanban webhook |

## Error Handling

All endpoints return errors in the format:

```json
{
  "detail": "Error description"
}
```

Common HTTP status codes:
- `200` — Success
- `401` — Unauthorized (missing/invalid auth)
- `404` — Not found
- `429` — Rate limited
- `500` — Internal server error
