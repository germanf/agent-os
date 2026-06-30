#!/bin/bash

# pick-port.sh - Find an available port in role-specific range
# Usage: pick-port.sh <ROLE>
# Roles: fullstack (8800-8849), qa (8850-8899), ui (8900-8949)

set -euo pipefail

ROLE="${1:-fullstack}"

# Define port ranges per role
case "$ROLE" in
  fullstack)
    PORT_START=8800
    PORT_END=8849
    ;;
  qa)
    PORT_START=8850
    PORT_END=8899
    ;;
  ui)
    PORT_START=8900
    PORT_END=8949
    ;;
  *)
    echo "Error: Unknown role '$ROLE'. Must be: fullstack, qa, or ui" >&2
    exit 1
    ;;
esac

# Function to check if port is available
is_port_available() {
  local port=$1
  # Use /proc/net/tcp for faster checking (Linux-specific)
  if [[ -f /proc/net/tcp ]]; then
    # Convert port to hex for /proc/net/tcp lookup
    local port_hex=$(printf '%X' "$port")
    # Check if port appears in /proc/net/tcp (columns for listening ports)
    ! grep -q ":$(printf '%04X' "$port") " /proc/net/tcp
  else
    # Fallback: use netstat (slower but more portable)
    ! netstat -tlnp 2>/dev/null | grep -q ":$port "
  fi
}

# Find first available port in range
for port in $(seq "$PORT_START" "$PORT_END"); do
  if is_port_available "$port"; then
    echo "$port"
    exit 0
  fi
done

# All ports in range are taken
echo "Error: All ports in range $PORT_START-$PORT_END are in use for role '$ROLE'" >&2
exit 1
