#!/bin/bash

# sandbox-up.sh - Spin up isolated Docker sandbox for agent
# Usage: sandbox-up.sh <ROLE> <WORKTREE_PATH> <AGENT_ID>
# Example: sandbox-up.sh fullstack /path/to/worktree agent-001

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SANDBOX_ROOT="$(dirname "$SCRIPT_DIR")"
PROJECT_ROOT="$(dirname "$SANDBOX_ROOT")"
TMP_DIR="$PROJECT_ROOT/tmp"

# Parameters
ROLE="${1:-}"
WORKTREE_PATH="${2:-}"
AGENT_ID="${3:-}"

# Validation
if [[ -z "$ROLE" ]]; then
  echo -e "${RED}Error: ROLE parameter required${NC}" >&2
  echo "Usage: $0 <ROLE> <WORKTREE_PATH> <AGENT_ID>" >&2
  echo "Roles: fullstack, qa, ui" >&2
  exit 1
fi

if [[ -z "$WORKTREE_PATH" ]]; then
  echo -e "${RED}Error: WORKTREE_PATH parameter required${NC}" >&2
  exit 1
fi

if [[ -z "$AGENT_ID" ]]; then
  echo -e "${RED}Error: AGENT_ID parameter required${NC}" >&2
  exit 1
fi

# Validate worktree path exists
if [[ ! -d "$WORKTREE_PATH" ]]; then
  echo -e "${RED}Error: Worktree path does not exist: $WORKTREE_PATH${NC}" >&2
  exit 1
fi

# Get absolute path
WORKTREE_PATH="$(cd "$WORKTREE_PATH" && pwd)"

echo -e "${YELLOW}Starting sandbox for agent: $AGENT_ID (role: $ROLE)${NC}"
echo "Worktree: $WORKTREE_PATH"

# Step 1: Build docker image if not exists
echo -e "${YELLOW}Step 1: Building Docker image...${NC}"
docker build -f "$SANDBOX_ROOT/Dockerfile.base" -t claude-sandbox:latest "$SANDBOX_ROOT" > /dev/null 2>&1 || {
  echo -e "${RED}Error: Docker build failed${NC}" >&2
  exit 1
}
echo -e "${GREEN}Docker image built successfully${NC}"

# Step 2: Pick available port
echo -e "${YELLOW}Step 2: Picking available port for role '$ROLE'...${NC}"
PORT=$("$SCRIPT_DIR/pick-port.sh" "$ROLE") || {
  echo -e "${RED}Error: Failed to pick port${NC}" >&2
  exit 1
}
echo -e "${GREEN}Selected port: $PORT${NC}"

# Step 3: Generate docker-compose.yml with port binding
echo -e "${YELLOW}Step 3: Generating docker-compose configuration...${NC}"
COMPOSE_FILE="$TMP_DIR/.docker-compose.${AGENT_ID}.yml"

# Create temporary compose file with port binding
cat > "$COMPOSE_FILE" << EOF
version: '3.9'

services:
  claude-sandbox:
    image: claude-sandbox:latest
    container_name: "claude-sandbox-${AGENT_ID}"

    environment:
      PORT: "$PORT"
      ROLE: "$ROLE"
      AGENT_ID: "$AGENT_ID"
      ENVIRONMENT: "sandbox"

    volumes:
      - "$WORKTREE_PATH:/app:rw"
      - "venv-${AGENT_ID}:/app/.venv"
      - "node-modules-${AGENT_ID}:/app/node_modules"

    networks:
      - sandbox-${ROLE}

    ports:
      - "127.0.0.1:${PORT}:${PORT}"

    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
        labels: "agent=${AGENT_ID},role=${ROLE}"

    stdin_open: true
    tty: true

networks:
  sandbox-fullstack:
    driver: bridge
    name: sandbox-fullstack
  sandbox-qa:
    driver: bridge
    name: sandbox-qa
  sandbox-ui:
    driver: bridge
    name: sandbox-ui

volumes:
  venv-${AGENT_ID}:
  node-modules-${AGENT_ID}:
EOF

echo -e "${GREEN}Compose configuration created at: $COMPOSE_FILE${NC}"

# Step 4: Start container
echo -e "${YELLOW}Step 4: Starting Docker container...${NC}"
if ! docker-compose -f "$COMPOSE_FILE" up -d > /dev/null 2>&1; then
  echo -e "${RED}Error: Docker container failed to start${NC}" >&2
  # Cleanup on failure
  "$SCRIPT_DIR/sandbox-down.sh" "$AGENT_ID" > /dev/null 2>&1 || true
  rm -f "$COMPOSE_FILE"
  exit 1
fi
echo -e "${GREEN}Container started: claude-sandbox-${AGENT_ID}${NC}"
echo -e "${GREEN}Port mapping: http://127.0.0.1:${PORT}${NC}"

# Step 5: Wait for container to be ready
echo -e "${YELLOW}Step 5: Waiting for container to be ready...${NC}"
sleep 2

# Check if container is still running
if ! docker ps --filter "name=claude-sandbox-${AGENT_ID}" | grep -q "claude-sandbox-${AGENT_ID}"; then
  echo -e "${RED}Error: Container exited unexpectedly${NC}" >&2
  "$SCRIPT_DIR/sandbox-down.sh" "$AGENT_ID" > /dev/null 2>&1 || true
  rm -f "$COMPOSE_FILE"
  exit 1
fi

# Step 5.5: Register sandbox in .running (track active containers)
RUNNING_FILE="$SANDBOX_ROOT/.running"
CONTAINER_NAME="claude-sandbox-${AGENT_ID}"
echo "$AGENT_ID $CONTAINER_NAME $WORKTREE_PATH $(date +%s)" >> "$RUNNING_FILE"
echo -e "${GREEN}Sandbox registered in tracking file${NC}"

# Step 6: Run ci-checks inside container
echo -e "${YELLOW}Step 6: Running CI checks inside container...${NC}"
if docker exec "claude-sandbox-${AGENT_ID}" bash /app/sandbox/scripts/ci-checks.sh; then
  echo -e "${GREEN}CI checks PASSED${NC}"
  CI_RESULT=0
else
  echo -e "${YELLOW}Warning: CI checks FAILED (but container is running)${NC}"
  CI_RESULT=1
fi

# Step 7: Report success
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Sandbox Setup Complete${NC}"
echo -e "${GREEN}========================================${NC}"
echo "Agent ID: $AGENT_ID"
echo "Role: $ROLE"
echo "Port: $PORT"
echo "Access: http://127.0.0.1:${PORT}"
echo "Logs: docker logs claude-sandbox-${AGENT_ID}"
echo "Shell: docker exec -it claude-sandbox-${AGENT_ID} bash"
echo ""

# Return exit code based on CI checks
exit "$CI_RESULT"
