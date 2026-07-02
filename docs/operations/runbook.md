# Runbook — Agent OS Operations

## Architecture

```
Internet → nginx (443/80) → uvicorn (8765) → FastAPI app
                                     ├── dashboard/data/chat.db (SQLite)
                                     ├── dashboard/data/logs/ (log rotation)
                                     └── dashboard/data/backups/ (auto backups)
```

Health checks run at startup and every request to `/api/health`.

## Health Endpoints

| Endpoint | What it checks | Auth |
|----------|---------------|------|
| `GET /api/health` | DB, Hermes, frontend build, disk | No |
| `GET /api/diagnostics` | Full platform diagnostics | No |
| `GET /api/alerts` | Active alerts | Yes |

## Restart

```bash
# Full restart
sudo systemctl restart agent-os

# Check status
sudo systemctl status agent-os

# View logs
journalctl -u agent-os -f
```

## Backup

Automatic backups run every 6 hours to `dashboard/data/backups/`. Retention: 7 days.

### Manual backup

```bash
python3 -c "from dashboard.backup import run_backup; run_backup()"
```

### Restore from backup

```bash
bash dashboard/restore.sh dashboard/data/backups/chat.db.20260702_120000.backup
```

Restore steps:
1. Stop the app: `sudo systemctl stop agent-os`
2. Run restore script
3. Verify: `sqlite3 dashboard/data/chat.db "SELECT COUNT(*) FROM messages"`
4. Start the app: `sudo systemctl start agent-os`
5. If restore fails, the previous DB is at `dashboard/data/chat.db.prev`

## Common Failures

### DB corrupt

Symptom: `GET /api/health` shows database as unavailable.
Fix: Restore from latest backup.

### Frontend not loading

Symptom: SPA returns blank page or "API running — frontend not built".
Fix: `cd dashboard/frontend && pnpm run build` then restart.

### Hermes not available

Symptom: `/api/health` shows hermes as unavailable. Chat still works using raw backend.
Fix: Check `hermes` CLI is installed and authenticated: `hermes --version`.

### Disk space low

Symptom: `/api/health` shows disk degraded or unavailable.
Fix: `journalctl --vacuum-size=500M`, prune old backups, check logs.

### Rate limiting too aggressive

Symptom: Users get 429 responses on normal usage.
Fix: Adjust limits in `dashboard/rate_limit.py` or set env vars.

## Monitoring

- Health checks at `/api/health` — poll every 30s from monitoring
- Alerts at `/api/alerts` — check for unacknowledged critical alerts
- Logs: `dashboard/data/logs/dashboard_YYYY-MM-DD.log` (rotated daily, 100MB max, retained 30 days)
- JSON log format: set `LOG_JSON=1` in env

## Escalation

| Issue | Contact |
|-------|---------|
| App down | System admin |
| Data loss | System admin + backup recovery |
| Security incident | System admin |
