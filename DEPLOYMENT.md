# Deployment Guide

This guide covers the production deployment of the Agentic Software Boutique on a Ubuntu VM with nginx, uvicorn, and systemd.

## Environment

- **OS**: Ubuntu 20.04+ (or equivalent)
- **Network**: VPN-only (WireGuard subnet `10.0.0.0/24`)
- **Reverse Proxy**: nginx
- **Application Server**: uvicorn (FastAPI)
- **Firewall**: iptables (persistent via `netfilter-persistent`)

## Prerequisites

Before running `dashboard/start.sh`, ensure:

1. **Node.js & pnpm** are installed (required for frontend build):
   ```bash
   # Example: install via nvm
   curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
   nvm install 18
   nvm use 18
   ```

2. **Python 3.9+** is available:
   ```bash
   python3 --version
   ```

3. **nginx** is installed:
   ```bash
   sudo apt-get install nginx
   sudo systemctl enable nginx
   ```

4. **iptables-persistent** is installed (to persist firewall rules):
   ```bash
   sudo apt-get install iptables-persistent netfilter-persistent
   ```

## Firewall Configuration (iptables)

The dashboard is restricted to the VPN subnet (`10.0.0.0/24`) at the firewall level.

### Step 1: Add firewall rules for HTTP and HTTPS

```bash
# Allow HTTP (port 80) from VPN subnet
sudo iptables -A INPUT -p tcp -s 10.0.0.0/24 --dport 80 -j ACCEPT

# Allow HTTPS (port 443) from VPN subnet
sudo iptables -A INPUT -p tcp -s 10.0.0.0/24 --dport 443 -j ACCEPT

# Persist the changes
sudo netfilter-persistent save
```

Verify the rules are in place:
```bash
sudo iptables -L -n | grep -E "80|443"
```

## SSL/TLS Certificate

The dashboard uses a **self-signed certificate** for internal VPN-only use.

### Self-Signed Certificate

The `dashboard/start.sh` script automatically generates a 10-year self-signed certificate if one doesn't exist:

```bash
# Generated at:
/etc/nginx/ssl/agentic-boutique-selfsigned.crt
/etc/nginx/ssl/agentic-boutique-selfsigned.key
```

**Browser Warning**: Users will see a certificate warning when accessing via HTTPS for the first time per device. This is expected and normal for self-signed certificates on internal tools — click "Advanced" and "Proceed" (or equivalent) to trust the certificate once.

### Future: Let's Encrypt Integration (Optional)

If you plan to migrate to a Let's Encrypt certificate:

1. Set up `certbot`:
   ```bash
   sudo apt-get install certbot python3-certbot-nginx
   ```

2. Update `dashboard/nginx.conf` to use Let's Encrypt paths:
   ```nginx
   ssl_certificate     /etc/letsencrypt/live/<your-domain>/fullchain.pem;
   ssl_certificate_key /etc/letsencrypt/live/<your-domain>/privkey.pem;
   ```

3. Run the renewal process:
   ```bash
   sudo certbot renew --nginx
   ```

Note: Let's Encrypt requires a publicly accessible domain and is not suitable for RFC1918 IPs.

## Deployment Steps

### 1. Clone the repository

```bash
git clone https://github.com/your-user/agentic-software-boutique.git
cd agentic-software-boutique
```

### 2. Run the deployment script

```bash
bash dashboard/start.sh
```

This script will:
- Create a Python virtual environment
- Install Python dependencies
- Build the frontend (pnpm install --frozen-lockfile + pnpm run build)
- Generate/verify the self-signed SSL certificate
- Install and configure nginx
- Set up the uvicorn systemd service
- Start the application

### 3. Verify deployment

```bash
# Check service status
sudo systemctl status agentic-software-boutique.service

# View logs
sudo journalctl -f -u agentic-software-boutique.service

# Test HTTP→HTTPS redirect
curl -i http://10.0.0.227/
# Should return: HTTP/1.1 307 Temporary Redirect
# Location: https://10.0.0.227/

# Test HTTPS access
curl -k https://10.0.0.227/api/health
# Should return: {"status":"ok","timestamp":...}
```

## HTTPS Enforcement

As of Task #6, the dashboard enforces HTTPS-only access:

- **HTTP (port 80)**: All requests redirect to HTTPS (307 Temporary Redirect)
  - Exception: `/.well-known/acme-challenge/` passes through for Let's Encrypt renewal
- **HTTPS (port 443)**: Responds with `Strict-Transport-Security` header (max-age=1 year)

### Security Implications

1. **Threat Model**: VPN-only (traffic already encrypted at layer 3), but HTTPS adds:
   - Application-level encryption (defense-in-depth)
   - Certificate pinning opportunity (future)
   - Browser security features (HSTS, CSP, etc.)

2. **HSTS and Self-Signed Certs**: RFC 6797 Section 7.4 states that browsers ignore the HSTS header when a certificate has errors (e.g., self-signed, untrusted). The header is still included for future integration with a trusted CA (Let's Encrypt).

3. **Authentication**: The dashboard uses Basic Authentication (HTTP `Authorization` header) over HTTPS. Never use over plain HTTP.

## Troubleshooting

### Service fails to start

1. Check logs:
   ```bash
    sudo journalctl -u agentic-software-boutique.service -n 50 --no-pager
   ```

2. Verify nginx config:
   ```bash
   sudo nginx -t
   ```

3. Verify uvicorn can bind to port 8765:
   ```bash
   sudo netstat -tulpn | grep 8765
   ```

### HTTPS redirect loop

- Verify nginx config syntax: `sudo nginx -t`
- Ensure the 443 block is configured correctly
- Check `proxy_set_header X-Forwarded-Proto https;` is present in the 443 block

### Firewall blocks traffic

- Verify iptables rules: `sudo iptables -L -n | grep -E "80|443"`
- Ensure rules persist: `sudo netfilter-persistent save`
- Check if ufw is interfering: `sudo systemctl status ufw` (should be inactive)

### Certificate warnings

- Self-signed: Normal. Trust once per device.
- Expired: Regenerate with `sudo rm /etc/nginx/ssl/agentic-boutique-selfsigned.*` and rerun `dashboard/start.sh`

## Updating the Deployment

After pushing changes to the repository:

```bash
cd /path/to/deployment
git pull --ff-only
bash dashboard/start.sh
```

The script is idempotent — it's safe to run multiple times.

## Monitoring

### Application Logs

```bash
# Follow real-time logs
sudo journalctl -f -u agentic-software-boutique.service

# View recent logs (100 lines)
sudo journalctl -u agentic-software-boutique.service -n 100 --no-pager

# View nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Health Check

The API exposes a health endpoint:

```bash
curl -k https://10.0.0.227/api/health
```

Returns: `{"status": "ok", "timestamp": <unix-timestamp>}`

## Security Checklist

- [ ] Firewall rules configured (iptables for ports 80/443)
- [ ] Self-signed certificate generated and in `/etc/nginx/ssl/`
- [ ] nginx config installed at `/etc/nginx/sites-enabled/agentic-boutique`
- [ ] uvicorn service running (`sudo systemctl status agentic-software-boutique`)
- [ ] HTTP redirects to HTTPS: `curl -i http://10.0.0.227/` → 307 redirect
- [ ] HSTS header present: `curl -kI https://10.0.0.227/ | grep Strict-Transport`
- [ ] Credentials file permissions are 0600: `ls -la dashboard/.credentials.json`
- [ ] Environment files are gitignored and not in version control
- [ ] VPN-only access enforced (allow/deny in nginx.conf)

## Support

For issues or questions, check:
- Deployment logs: `tail -f dashboard/deploy.log`
- Service logs: `sudo journalctl -u agentic-software-boutique.service`
- nginx config: `cat /etc/nginx/sites-enabled/agentic-boutique`
