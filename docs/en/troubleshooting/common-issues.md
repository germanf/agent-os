# Troubleshooting Guide

## Backend Won't Start

| Symptom | Possible Cause | Resolution |
|---------|---------------|------------|
| `Address already in use` | Port 8765 occupied | `lsof -ti:8765 \| xargs kill -9` |
| `ModuleNotFoundError` | Missing dependencies | `pip install -r requirements.txt` |
| `DASH_USER not set` | Auth not configured | Set `DASH_USER` and `DASH_PASS` env vars |
| `sqlite3.OperationalError` | DB corruption | Restore from backup: `bash dashboard/restore.sh` |

## Frontend Build Fails

| Symptom | Possible Cause | Resolution |
|---------|---------------|------------|
| `tsc errors` | TypeScript type mismatch | Check type errors and fix |
| `Module not found` | Missing dependencies | `pnpm install` |
| `Build hangs` | Memory constraint | Increase Node memory: `NODE_OPTIONS=--max-old-space-size=4096 pnpm run build` |

## Chat Not Working

| Symptom | Possible Cause | Resolution |
|---------|---------------|------------|
| Claude not responding | Claude CLI not installed | Install Claude Code: `pip install claude-code` |
| `claude: command not found` | CLI not in PATH | Ensure Claude is installed and in PATH |
| Chat returns empty | No backend selected | Check `CHAT_BACKEND` env var |
| SSE stream stalls | Buffering enabled | Ensure nginx `proxy_buffering off` |

## Notes Not Loading

| Symptom | Possible Cause | Resolution |
|---------|---------------|------------|
| Empty tree | Vault not configured | Set `VAULT_DIR` environment variable |
| Path traversal error | Invalid path | Only alphanumeric chars, hyphens, underscores, slashes, dots |
| File not found | Path doesn't exist | Check the exact path in vault |

## Orchestrator Issues

| Symptom | Possible Cause | Resolution |
|---------|---------------|------------|
| Tasks stay queued | No agents available | Check agent pool health: `GET /api/orchestrator/agents` |
| Task fails | Agent unresponsive | Verify agent process is running |
| DAG deadlock | Circular dependency | Check task graph for cycles |
| SSE events not received | Client disconnected | Reconnect to stream |

## Database Issues

| Symptom | Possible Cause | Resolution |
|---------|---------------|------------|
| `database is locked` | Concurrent writes | SQLite WAL mode should prevent this; check for long-running transactions |
| `no such table` | DB not initialized | Access any endpoint to trigger auto-init |
| Disk space | Growing DB file | Backups are kept 7 days; prune manually if needed |

## Rate Limiting

If you receive `429 Too Many Requests`, wait 60 seconds and retry. Rate limits are:

- `/api/health`: 60/minute
- Most endpoints: 30/minute
- Mutations (POST/PATCH/DELETE): 10/minute

## Getting Help

1. Check this troubleshooting guide
2. Review the [Operations Runbook](../../operations/runbook.md)
3. Open a GitHub issue with:
   - Full error message and stack trace
   - Steps to reproduce
   - Environment details (OS, Python version, Node version)
