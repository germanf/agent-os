#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$SCRIPT_DIR/.venv"
VENV_NEW="$SCRIPT_DIR/.venv.new"
NGINX_CONF="/etc/nginx/sites-enabled/agentic-boutique"
SYSTEMD_UNIT="/etc/systemd/system/agentic-software-boutique.service"
VENV_PYTHON="$VENV/bin/python3"
LOG_FILE="$SCRIPT_DIR/deploy.log"

# Initialize log
{
  echo "=== Deploy started at $(date) ==="
  echo "Script directory: $SCRIPT_DIR"
} > "$LOG_FILE"

log() {
  echo "[$(date '+%H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

error() {
  echo "[ERROR] $*" | tee -a "$LOG_FILE" >&2
  # Cleanup temp venv on error
  if [[ -d "$VENV_NEW" ]]; then
    log "Cleaning up temporary venv..."
    rm -rf "$VENV_NEW"
  fi
  exit 1
}

# ── Frontend (validate in temp location first) ─────────────────────────────────
log "Validating frontend build..."
if ! command -v pnpm &>/dev/null; then
  error "pnpm not found. Install Node.js + pnpm (e.g., via nvm + corepack) on this VM"
fi

FRONTEND_DIR="$SCRIPT_DIR/frontend"
DIST_DIR="$FRONTEND_DIR/dist"

if [[ ! -d "$FRONTEND_DIR" ]]; then
  error "Frontend directory not found at $FRONTEND_DIR"
fi

if ! (cd "$FRONTEND_DIR" && pnpm install --frozen-lockfile >> "$LOG_FILE" 2>&1 && pnpm run build >> "$LOG_FILE" 2>&1); then
  error "Frontend build failed. Check $LOG_FILE for details"
fi

if [[ ! -f "$DIST_DIR/index.html" ]]; then
  error "Frontend build succeeded but index.html not found at $DIST_DIR/index.html"
fi

log "✓ Frontend built successfully at $DIST_DIR"

# ── Python venv (safe replacement) ─────────────────────────────────────────────
log "Setting up Python virtual environment..."

log "Creating new virtual environment in $VENV_NEW..."
if ! python3 -m venv "$VENV_NEW" >> "$LOG_FILE" 2>&1; then
  error "Failed to create new venv"
fi

VENV_PYTHON_NEW="$VENV_NEW/bin/python3"
if [[ ! -f "$VENV_PYTHON_NEW" ]]; then
  error "Python executable not found at $VENV_PYTHON_NEW"
fi

source "$VENV_NEW/bin/activate" || error "Failed to activate new venv"

log "Upgrading pip in new venv..."
if ! pip install --upgrade pip setuptools wheel >> "$LOG_FILE" 2>&1; then
  log "⚠ Warning: pip upgrade had issues, continuing anyway..."
fi

log "Installing dependencies from requirements.txt..."
if ! pip install -r "$SCRIPT_DIR/requirements.txt" >> "$LOG_FILE" 2>&1; then
  error "Failed to install Python dependencies. Check $LOG_FILE for details"
fi

# Verify critical packages
log "Verifying critical packages..."
for pkg in fastapi uvicorn python-multipart aiofiles; do
  if ! "$VENV_PYTHON_NEW" -c "import ${pkg//-/_}" 2>/dev/null; then
    error "Missing package: $pkg"
  fi
done
log "✓ All critical packages installed"

# Swap venvs: old -> backup, new -> active
log "Swapping virtual environments..."
if [[ -d "$VENV" ]]; then
  log "Removing old venv..."
  rm -rf "$VENV"
fi

mv "$VENV_NEW" "$VENV" || error "Failed to move new venv into place"
log "✓ Virtual environment updated successfully"

# ── Self-signed TLS cert (idempotent) ───────────────────────────────────────────
# Needed for the Web Speech API (mic input), which requires a secure context in
# most browsers. speechSynthesis (spoken output) doesn't need this, but both
# ship together. openssl (not mkcert) so this stays fully self-contained — no
# manual install step on the VM. Browsers will show a one-time trust warning
# per device; that's expected for a VPN-only internal tool, not worked around.
log "Setting up TLS certificate..."
SSL_DIR="/etc/nginx/ssl"
SSL_CERT="$SSL_DIR/agentic-boutique-selfsigned.crt"
SSL_KEY="$SSL_DIR/agentic-boutique-selfsigned.key"
if [[ ! -f "$SSL_CERT" || ! -f "$SSL_KEY" ]]; then
  log "Generating self-signed TLS certificate..."
  sudo mkdir -p "$SSL_DIR"
  sudo openssl req -x509 -nodes -days 3650 \
    -newkey rsa:2048 \
    -keyout "$SSL_KEY" -out "$SSL_CERT" \
    -subj "/CN=10.0.0.227" >> "$LOG_FILE" 2>&1 || error "Failed to generate TLS cert"
  log "✓ TLS certificate generated"
else
  log "✓ TLS certificate already exists"
fi

# ── NGINX ──────────────────────────────────────────────────────────────────────
log "Configuring NGINX..."
sudo cp "$SCRIPT_DIR/nginx.conf" "$NGINX_CONF" || error "Failed to install NGINX config"

# Disable default site if it's listening on port 80 (would conflict)
if [[ -L /etc/nginx/sites-enabled/default ]]; then
  sudo rm -f /etc/nginx/sites-enabled/default
  log "Disabled NGINX default site"
fi

log "Testing NGINX configuration..."
if ! sudo nginx -t >> "$LOG_FILE" 2>&1; then
  error "NGINX configuration test failed. Check $LOG_FILE"
fi

log "Reloading NGINX..."
if ! sudo systemctl reload nginx >> "$LOG_FILE" 2>&1; then
  error "Failed to reload NGINX"
fi
log "✓ NGINX reloaded successfully"

# ── Uvicorn (systemd service) ───────────────────────────────────────────────────
# Managed by systemd (not nohup) so it survives the deploy job ending — a
# self-hosted GitHub Actions runner kills any process still attached to the
# job's process group/cgroup as soon as the job completes, which a plain
# nohup'd background process does not escape.
log "Installing systemd service..."
sudo cp "$SCRIPT_DIR/agentic-software-boutique.service" "$SYSTEMD_UNIT" || error "Failed to install systemd unit"

# Inject HTTP Auth credentials from .env (written by deploy workflow)
_ENV_FILE="$SCRIPT_DIR/.env"
if [[ -f "$_ENV_FILE" ]]; then
  _DASH_USER=$(grep '^DASH_USER=' "$_ENV_FILE" | cut -d= -f2- | head -1)
  _DASH_PASS=$(grep '^DASH_PASS=' "$_ENV_FILE" | cut -d= -f2- | head -1)
  if [[ -n "$_DASH_USER" && -n "$_DASH_PASS" ]]; then
    _USER_ESC=$(printf '%s' "$_DASH_USER" | sed 's/[&|\\]/\\&/g')
    _PASS_ESC=$(printf '%s' "$_DASH_PASS" | sed 's/[&|\\]/\\&/g')
    sudo sed -i "s|^# Environment=\"DASH_USER=.*\"|Environment=\"DASH_USER=$_USER_ESC\"|" "$SYSTEMD_UNIT"
    sudo sed -i "s|^# Environment=\"DASH_PASS=.*\"|Environment=\"DASH_PASS=$_PASS_ESC\"|" "$SYSTEMD_UNIT"
    log "✓ HTTP Auth credentials injected into systemd service"
  else
    log "⚠️  WARNING: .env exists but DASH_USER/DASH_PASS are empty"
  fi
fi

sudo systemctl daemon-reload || error "Failed to reload systemd daemon"
sudo systemctl enable agentic-software-boutique.service || error "Failed to enable service"

log "Testing Python app startup..."

# Pre-flight filesystem checks
log "Checking data directory permissions..."
DATA_DIR="$SCRIPT_DIR/data"
if [[ ! -d "$DATA_DIR" ]]; then
  log "Creating data directory..."
  mkdir -p "$DATA_DIR" || error "Failed to create $DATA_DIR"
fi

if [[ ! -w "$DATA_DIR" ]]; then
  error "Data directory is not writable: $DATA_DIR"
fi

UPLOADS_DIR="$DATA_DIR/uploads"
if [[ ! -d "$UPLOADS_DIR" ]]; then
  mkdir -p "$UPLOADS_DIR" || error "Failed to create uploads directory"
fi

log "✓ Data directories ready"

# ── HTTP Auth Credentials ───────────────────────────────────────────────────────
log "Checking HTTP Auth configuration..."

# Check if credentials are configured in systemd service
if ! grep -q "^Environment=\"DASH_USER=" "$SYSTEMD_UNIT" 2>/dev/null; then
  log "⚠️  WARNING: DASH_USER not configured in systemd service"
  log "   Edit: sudo systemctl edit agentic-software-boutique.service"
  log "   And uncomment/set the DASH_USER and DASH_PASS environment variables"
  log "   See dashboard/AUTHENTICATION.md for details"
fi

if ! grep -q "^Environment=\"DASH_PASS=" "$SYSTEMD_UNIT" 2>/dev/null; then
  log "⚠️  WARNING: DASH_PASS not configured in systemd service"
  log "   Edit: sudo systemctl edit agentic-software-boutique.service"
  log "   And uncomment/set the DASH_USER and DASH_PASS environment variables"
  log "   See dashboard/AUTHENTICATION.md for details"
fi

# Use a dedicated test script that provides detailed diagnostics
if "$VENV_PYTHON" "$SCRIPT_DIR/tests/test_fastapi_minimal.py" 2>&1 | tee -a "$LOG_FILE"; then
  log "✓ App startup test passed"
else
  EXIT_CODE=$?
  log ""
  log "❌ FAILED: FastAPI app failed to import (exit code: $EXIT_CODE)"
  log "See error output above for details"
  exit 1
fi

log "Starting uvicorn service..."
sudo systemctl restart agentic-software-boutique.service || {
  EXIT=$?
  log "⚠ systemctl restart failed with exit code $EXIT"
  log "Attempting to capture error logs..."
  {
    echo ""
    echo "=== systemctl status output ==="
    sudo systemctl status agentic-software-boutique.service --no-pager 2>&1 || true
    echo ""
    echo "=== journalctl output (last 100 lines) ==="
    sudo journalctl -u agentic-software-boutique.service -n 100 --no-pager 2>&1 || true
  } | tee -a "$LOG_FILE"
  error "Failed to restart service. See logs above."
}

# Give service a moment to start
sleep 2

# Verify service is running
log "Verifying service is running..."
if ! sudo systemctl is-active agentic-software-boutique.service > /dev/null 2>&1; then
  log "⚠ Service is not active. Capturing detailed diagnostics..."
  {
    echo ""
    echo "=== Service Status ==="
    sudo systemctl status agentic-software-boutique.service --no-pager 2>&1 || true
    echo ""
    echo "=== Recent Journal Logs (100 lines) ==="
    sudo journalctl -u agentic-software-boutique.service -n 100 --no-pager 2>&1 || true
  } | tee -a "$LOG_FILE"
  error "Service failed to start or crashed. See logs above."
fi

# Verify uvicorn is listening
log "Verifying uvicorn is listening on port 8765..."
if ! timeout 5 bash -c 'echo > /dev/tcp/127.0.0.1/8765' 2>/dev/null; then
  log "⚠ Uvicorn not responding on port 8765. Checking service status..."
  {
    echo ""
    echo "=== Service Status ==="
    sudo systemctl status agentic-software-boutique.service --no-pager 2>&1 || true
    echo ""
    echo "=== Recent Logs ==="
    sudo journalctl -u agentic-software-boutique.service -n 50 --no-pager 2>&1 || true
  } | tee -a "$LOG_FILE"
  error "Uvicorn not listening on port 8765. Check logs above."
fi

log "✓ Uvicorn is listening on port 8765"

{
  echo ""
  echo "=== Deploy completed successfully at $(date) ==="
  echo "Dashboard running:"
  echo "  service     : agentic-software-boutique.service"
  echo "  local URL   : http://127.0.0.1:8765"
  echo "  VPN URL     : http://10.0.0.227"
  echo ""
  echo "View logs:"
  echo "  journalctl -f -u agentic-software-boutique.service"
  echo "  journalctl -f -u nginx"
  echo "  tail -f $LOG_FILE"
} | tee -a "$LOG_FILE"
