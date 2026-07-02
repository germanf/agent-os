# Production Deployment

## Stack

- **OS**: Ubuntu 20.04+ (VPN-only, WireGuard subnet `10.0.0.0/24`)
- **Web Server**: nginx (reverse proxy, HTTP→HTTPS redirect, SSL termination)
- **App Server**: uvicorn (port 8765, managed by systemd)
- **Database**: SQLite (WAL mode)
- **Firewall**: iptables (persisted via netfilter-persistent)

## One-Command Deploy

```bash
bash dashboard/start.sh
```

This idempotent script:

1. Builds the frontend (`pnpm install --frozen-lockfile && pnpm run build`)
2. Creates a Python virtual environment atomically (`.venv.new` → swap to `.venv`)
3. Installs Python dependencies from `requirements.txt`
4. Generates a self-signed TLS certificate (10-year validity)
5. Installs nginx configuration
6. Installs systemd service (`agentic-software-boutique.service`)
7. Injects `DASH_USER`/`DASH_PASS` from `.env` into the systemd unit
8. Runs pre-flight checks (data directory, Python app startup test)
9. Restarts uvicorn and verifies it's listening

## Manual Setup

### 1. System Dependencies

```bash
sudo apt update
sudo apt install nginx python3 python3-venv python3-pip netfilter-persistent iptables-persistent
```

### 2. nginx Configuration

The production `nginx.conf` is at `dashboard/nginx.conf`. Key settings:

```nginx
location / {
    proxy_pass http://127.0.0.1:8765;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;

    # SSE support (buffering off)
    proxy_buffering off;
    proxy_cache off;
    proxy_read_timeout 86400s;

    # Uploads
    client_max_body_size 55M;
}
```

### 3. systemd Service

The service file is at `dashboard/agentic-software-boutique.service`:

```ini
[Unit]
Description=Agentic Software Boutique
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/agent-os/dashboard
ExecStart=/home/ubuntu/agent-os/dashboard/.venv/bin/uvicorn dashboard.main:app --host 127.0.0.1 --port 8765 --workers 1
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### 4. TLS Certificate

Self-signed certificate generation (done by `start.sh`):

```bash
sudo mkdir -p /etc/nginx/ssl
sudo openssl req -x509 -nodes -days 3650 -newkey rsa:2048 \
  -keyout /etc/nginx/ssl/agentic-boutique-selfsigned.key \
  -out /etc/nginx/ssl/agentic-boutique-selfsigned.crt \
  -subj "/CN=agentic-boutique"
```

For production, replace with a real CA certificate.

### 5. Firewall

```bash
# Allow HTTP/HTTPS from VPN
sudo iptables -A INPUT -s 10.0.0.0/24 -p tcp --dport 80 -j ACCEPT
sudo iptables -A INPUT -s 10.0.0.0/24 -p tcp --dport 443 -j ACCEPT
# Allow app port from localhost only
sudo iptables -A INPUT -s 127.0.0.1 -p tcp --dport 8765 -j ACCEPT
# Save rules
sudo netfilter-persistent save
```

## Environment Variables

Set these in the systemd environment or in a `.env` file read by `start.sh`:

| Variable | Required | Description |
|----------|----------|-------------|
| `DASH_USER` | Yes | HTTP Basic Auth username |
| `DASH_PASS` | Yes | HTTP Basic Auth password |
| `LOG_JSON` | No | Enable JSON logs (set to any value) |
| `VAULT_DIR` | No | Path to Obsidian vault |

## Monitoring

### Health Checks

```bash
curl https://your-domain/api/health
# → {"status":"healthy","checks":{"db":"ok","frontend":"ok"},...}
```

### Diagnostics

```bash
curl -u user:pass https://your-domain/api/diagnostics
# → Full deployment health report
```

### Alerts

```bash
curl -u user:pass https://your-domain/api/alerts
# → List of active alerts
```

## Backup and Restore

Automatic backups run every 6 hours with 7-day retention:

```bash
# Manual backup
python3 -c "from dashboard.backup import manual_backup; manual_backup()"

# Restore
bash dashboard/restore.sh
```

## Logging

By default, logs are human-readable. Set `LOG_JSON=1` for JSON log serialization:

```bash
LOG_JSON=1 uvicorn dashboard.main:app --port 8765
```

JSON format: `{"time":"...", "level":"INFO", "event":"...", "module":"...", "context":{...}}`

## Operations Runbook

See `docs/operations/runbook.md` for:
- Restart procedures
- Backup/restore steps
- Common failure modes
- Escalation paths
