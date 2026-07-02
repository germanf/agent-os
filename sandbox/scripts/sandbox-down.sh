#!/bin/bash

# sandbox-down.sh - Tear down isolated Docker sandbox for agent
# Usage: sandbox-down.sh <AGENT_ID>
# Gracefully removes container and associated volumes

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
AGENT_ID="${1:-}"

# Validation
if [[ -z "$AGENT_ID" ]]; then
  echo -e "${RED}Error: AGENT_ID parameter required${NC}" >&2
  echo "Usage: $0 <AGENT_ID>" >&2
  exit 1
fi

# Set up signal handlers for graceful shutdown
cleanup() {
  echo -e "${YELLOW}Cleanup signal received, exiting gracefully...${NC}"
  exit 0
}
trap cleanup SIGINT SIGTERM

echo -e "${YELLOW}Tearing down sandbox for agent: $AGENT_ID${NC}"

# Find docker-compose file for this agent
COMPOSE_FILE="$TMP_DIR/.docker-compose.${AGENT_ID}.yml"

if [[ ! -f "$COMPOSE_FILE" ]]; then
  echo -e "${YELLOW}Warning: Compose file not found at $COMPOSE_FILE${NC}"
  # Continue with container name-based cleanup
else
  echo "Using compose file: $COMPOSE_FILE"
fi

# Check if container exists
CONTAINER_NAME="claude-sandbox-${AGENT_ID}"
if ! docker ps -a --filter "name=$CONTAINER_NAME" | grep -q "$CONTAINER_NAME"; then
  echo -e "${YELLOW}Container not found: $CONTAINER_NAME${NC}"
  # Continue to cleanup files
else
  # Step 1: Stop container if running
  echo -e "${YELLOW}Step 1: Stopping container...${NC}"
  if docker ps --filter "name=$CONTAINER_NAME" | grep -q "$CONTAINER_NAME"; then
    if docker stop "$CONTAINER_NAME" > /dev/null 2>&1; then
      echo -e "${GREEN}Container stopped${NC}"
    else
      echo -e "${YELLOW}Warning: Failed to stop container (may already be stopped)${NC}"
    fi
  fi

  # Step 2: Remove container and volumes
  echo -e "${YELLOW}Step 2: Removing container and volumes...${NC}"
  if [[ -f "$COMPOSE_FILE" ]]; then
    # Use docker-compose to remove (also handles named volumes)
    if docker-compose -f "$COMPOSE_FILE" down -v > /dev/null 2>&1; then
      echo -e "${GREEN}Container and volumes removed via docker-compose${NC}"
    else
      # Fallback: remove manually
      docker rm -f "$CONTAINER_NAME" > /dev/null 2>&1 || true
      docker volume rm "venv-${AGENT_ID}" > /dev/null 2>&1 || true
      docker volume rm "node-modules-${AGENT_ID}" > /dev/null 2>&1 || true
      echo -e "${GREEN}Container and volumes removed manually${NC}"
    fi
  else
    # Remove manually without compose file
    docker rm -f "$CONTAINER_NAME" > /dev/null 2>&1 || true
    docker volume rm "venv-${AGENT_ID}" > /dev/null 2>&1 || true
    docker volume rm "node-modules-${AGENT_ID}" > /dev/null 2>&1 || true
    echo -e "${GREEN}Container and volumes removed${NC}"
  fi
fi

# Step 3: Clean up compose file
echo -e "${YELLOW}Step 3: Cleaning up compose configuration...${NC}"
if [[ -f "$COMPOSE_FILE" ]]; then
  if rm -f "$COMPOSE_FILE"; then
    echo -e "${GREEN}Compose file removed: $COMPOSE_FILE${NC}"
  else
    echo -e "${YELLOW}Warning: Failed to remove compose file${NC}"
  fi
fi

# Step 4: Remove entry from .running file (cleanup tracking)
RUNNING_FILE="$SANDBOX_ROOT/.running"
if [[ -f "$RUNNING_FILE" ]]; then
  sed -i "/^${AGENT_ID} /d" "$RUNNING_FILE"
  # Remove the file if it's now empty
  if [[ ! -s "$RUNNING_FILE" ]]; then
    rm -f "$RUNNING_FILE"
  fi
fi

# Step 5: Final report
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Sandbox Teardown Complete${NC}"
echo -e "${GREEN}========================================${NC}"
echo "Agent ID: $AGENT_ID"
echo "Status: Cleaned up"
echo ""

exit 0
