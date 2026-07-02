# Environment Configuration

## Environment Variables

| Variable | Default | Required | Description |
|----------|---------|----------|-------------|
| `DASH_USER` | — | Yes | HTTP Basic Auth username |
| `DASH_PASS` | — | Yes | HTTP Basic Auth password |
| `CHAT_BACKEND` | `claude` | No | Preferred chat backend: `claude`, `opencode`, `codex`, `kimi` |
| `HEADROOM_PORT` | `8787` | No | Headroom proxy port |
| `HEADROOM_HOST` | `127.0.0.1` | No | Headroom proxy host |
| `HEADROOM_LEARN_INTERVAL_HOURS` | `168` | No | Learning loop interval (hours, default 7 days) |
| `HEADROOM_STATELESS` | `true` | No | Headroom stateless mode |
| `OPCODE_SERVER_PORT` | `8899` | No | OpenCode server port |
| `OPCODE_SERVER_HOST` | `127.0.0.1` | No | OpenCode server host |
| `HERMES_CURATOR_INTERVAL_HOURS` | `24` | No | Curator review loop interval |
| `PLATFORM_CRON_TICK_INTERVAL` | `30` | No | Cron tick interval in seconds |
| `LOG_JSON` | — | No | Enable JSON log serialization (set to any value) |
| `VAULT_DIR` | `/home/ubuntu/vault` | No | Obsidian vault directory path |

## Configuration Files

| File | Purpose |
|------|---------|
| `dashboard/.credentials.json` | Alternative to `DASH_USER`/`DASH_PASS` env vars |
| `dashboard/.env` | Environment variable definitions (gitignored) |
| `dashboard/nginx.conf` | Production nginx reverse proxy config |
| `dashboard/agentic-software-boutique.service` | systemd unit file |

## Secrets Management

- All credential files (`.credentials.json`, `.env`) are gitignored with `chmod 0600`
- API secrets are masked as `••••••••` when returned from GET endpoints
- POST endpoints preserve existing values when masked values are submitted
- Never hardcode credentials in source files

## Setting Up Authentication

### Option 1: Environment Variables
```bash
export DASH_USER=admin
export DASH_PASS=securepassword
uvicorn dashboard.main:app --port 8765 --reload
```

### Option 2: Credentials File
Create `dashboard/.credentials.json`:
```json
{
  "username": "admin",
  "password": "securepassword"
}
```
Set permissions: `chmod 600 dashboard/.credentials.json`

## Recommended Practices

- Use environment variables for production (injected via `.env` or systemd unit)
- Rotate credentials regularly
- Use strong passwords (32+ characters recommended for internet-facing instances)
- Never commit credential files to version control
- For VPN-only deployments, the VPN subnet provides an additional security layer
