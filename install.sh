#!/usr/bin/env bash
set -euo pipefail

REPO="https://github.com/germanf/agent-os.git"
TARGET_DIR="${HOME}/agent-os"
DASH_USER="${DASH_USER:-admin}"
DASH_PASS="${DASH_PASS:-}"
PORT="${PORT:-8765}"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m'

info()  { printf "${GREEN}%s${NC}\n" "$*"; }
warn()  { printf "${YELLOW}⚠ %s${NC}\n" "$*"; }
err()   { printf "${RED}✗ %s${NC}\n" "$*"; }
header(){ printf "\n${BOLD}%s${NC}\n" "$*"; }

cleanup() {
    if [ -n "${UVID_PID:-}" ]; then
        kill "$UVID_PID" 2>/dev/null || true
    fi
}
trap cleanup EXIT

check_cmd() {
    if ! command -v "$1" &>/dev/null; then
        err "$1 is required but not found."
        case "$1" in
            python3) echo "  Install: apt install python3 python3-venv (Linux) or brew install python (macOS)" ;;
            node)    echo "  Install: https://nodejs.org/en/download/" ;;
            pnpm)    echo "  Install: npm install -g pnpm" ;;
            git)     echo "  Install: apt install git (Linux) or brew install git (macOS)" ;;
        esac
        return 1
    fi
}

header "Agentic Software Boutique — Bootstrap"

echo ""
info "Checking prerequisites..."

check_cmd python3
PY_VER=$(python3 --version 2>&1 | grep -oP '\d+\.\d+')
if [ "$(echo "$PY_VER" | cut -d. -f1)" -lt 3 ] || { [ "$(echo "$PY_VER" | cut -d. -f1)" -eq 3 ] && [ "$(echo "$PY_VER" | cut -d. -f2)" -lt 11 ]; }; then
    err "Python 3.11+ required, found $PY_VER"
    exit 1
fi
check_cmd node
check_cmd pnpm
check_cmd git

echo ""

info "Setting up project in ${TARGET_DIR}..."

if [ -d "$TARGET_DIR" ]; then
    warn "Directory exists — pulling latest changes..."
    cd "$TARGET_DIR"
    git pull --ff-only
else
    git clone --depth 1 "$REPO" "$TARGET_DIR"
    cd "$TARGET_DIR"
fi

echo ""

header "Python virtual environment"
python3 -m venv .venv
source .venv/bin/activate
pip install -q -r dashboard/requirements.txt

echo ""

header "Frontend build"
cd dashboard/frontend
pnpm install --frozen-lockfile 2>/dev/null || pnpm install
pnpm build
cd "$TARGET_DIR"

echo ""

header "Configuration"
ENV_FILE="${TARGET_DIR}/.env"
if [ -f "$ENV_FILE" ] && grep -q "DASH_USER" "$ENV_FILE" 2>/dev/null; then
    info "Existing .env found, preserving credentials"
else
    if [ -z "$DASH_PASS" ]; then
        if command -v openssl &>/dev/null; then
            DASH_PASS=$(openssl rand -hex 8)
        elif command -v uuidgen &>/dev/null; then
            DASH_PASS="$(uuidgen | head -c 16)"
        else
            DASH_PASS="change-me-$(date +%s)"
        fi
        warn "Generated random password: ${DASH_PASS}"
        echo "  (set DASH_PASS env var to use your own)"
    fi
    cat > "$ENV_FILE" <<ENVEOF
DASH_USER=${DASH_USER}
DASH_PASS=${DASH_PASS}
ENVEOF
    info "Created ${ENV_FILE}"
fi

echo ""

header "Starting server"
export DASH_USER DASH_PASS
nohup .venv/bin/uvicorn dashboard.main:app --host 0.0.0.0 --port "$PORT" > /tmp/agent-os.log 2>&1 &
UVID_PID=$!

# Wait for server
for i in $(seq 1 15); do
    if curl -sf "http://127.0.0.1:${PORT}/api/health" >/dev/null 2>&1; then
        echo ""
        info "╔══════════════════════════════════════════════════╗"
        info "║     Agency is running!                          ║"
        info "║                                                ║"
        printf "║  ${BOLD}URL:${NC}  http://localhost:${PORT}                      ║\n"
        printf "║  ${BOLD}User:${NC} ${DASH_USER}                                   ║\n"
        printf "║  ${BOLD}Pass:${NC} ${DASH_PASS}                   ║\n"
        info "║                                                ║"
        info "║  Stop: kill ${UVID_PID}                              ║"
        info "╚══════════════════════════════════════════════════╝"
        echo ""
        info "Logs: tail -f /tmp/agent-os.log"
        exit 0
    fi
    sleep 1
done

err "Server failed to start within 15s. Check /tmp/agent-os.log"
exit 1
