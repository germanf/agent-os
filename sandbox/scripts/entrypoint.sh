#!/bin/bash

# entrypoint.sh - Start uvicorn app in sandbox container
# Usage: entrypoint.sh [OPTIONAL_ARGS]
# Environment variables:
#   PORT - Port to listen on (default: 8765)

set -euo pipefail

PORT="${PORT:-8765}"

echo "Starting uvicorn application..."
echo "Port: $PORT"
echo "Working directory: $(pwd)"

# Additional arguments can be passed to uvicorn
EXTRA_ARGS="${@:-}"

# Start uvicorn
exec uvicorn dashboard.main:app \
  --host 0.0.0.0 \
  --port "$PORT" \
  --reload \
  $EXTRA_ARGS
