#!/bin/bash

# sandbox-cleanup-all.sh - Cleanup ALL agent sandboxes globally
# Finds all active containers matching pattern 'claude-sandbox-*'
# and removes them along with associated volumes and compose files

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

echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}Global Sandbox Cleanup${NC}"
echo -e "${YELLOW}========================================${NC}"

# Find all containers matching pattern
CONTAINERS=$(docker ps -a --format "table {{.Names}}" | grep "^claude-sandbox-" | sort)

if [[ -z "$CONTAINERS" ]]; then
  echo -e "${YELLOW}No active sandboxes found${NC}"
  exit 0
fi

# Count containers
CONTAINER_COUNT=$(echo "$CONTAINERS" | wc -l)
echo -e "${YELLOW}Found $CONTAINER_COUNT sandbox container(s) to clean up${NC}"
echo ""

# Track results
CLEANED_COUNT=0
FAILED_COUNT=0
FAILED_AGENTS=()

# Process each container
for CONTAINER_NAME in $CONTAINERS; do
  echo -e "${YELLOW}Cleaning up: $CONTAINER_NAME${NC}"

  # Extract AGENT_ID from container name (remove 'claude-sandbox-' prefix)
  AGENT_ID="${CONTAINER_NAME#claude-sandbox-}"

  # Run sandbox-down.sh for this agent
  if "$SCRIPT_DIR/sandbox-down.sh" "$AGENT_ID" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Cleaned up $AGENT_ID${NC}"
    ((CLEANED_COUNT++))
  else
    echo -e "${RED}✗ Failed to clean up $AGENT_ID${NC}"
    FAILED_AGENTS+=("$AGENT_ID")
    ((FAILED_COUNT++))
  fi
done

# Cleanup any orphaned compose files
echo ""
echo -e "${YELLOW}Checking for orphaned compose files...${NC}"
ORPHANED_COMPOSE=$(find "$TMP_DIR" -name ".docker-compose.*.yml" -type f 2>/dev/null | wc -l)

if [[ $ORPHANED_COMPOSE -gt 0 ]]; then
  echo -e "${YELLOW}Found $ORPHANED_COMPOSE orphaned compose file(s)${NC}"
  find "$TMP_DIR" -name ".docker-compose.*.yml" -type f -exec rm -f {} \;
  echo -e "${GREEN}Removed orphaned compose files${NC}"
fi

# Cleanup orphaned volumes
echo ""
echo -e "${YELLOW}Removing orphaned volumes...${NC}"
ORPHANED_VOLUMES=$(docker volume ls --format "table {{.Name}}" | grep -E "^(venv|node-modules)-" | wc -l)

if [[ $ORPHANED_VOLUMES -gt 0 ]]; then
  echo -e "${YELLOW}Found $ORPHANED_VOLUMES orphaned volume(s)${NC}"
  docker volume ls --format "table {{.Name}}" | grep -E "^(venv|node-modules)-" | xargs -r docker volume rm > /dev/null 2>&1 || true
  echo -e "${GREEN}Removed orphaned volumes${NC}"
fi

# Final report
echo ""
echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}Cleanup Summary${NC}"
echo -e "${YELLOW}========================================${NC}"
echo "Total processed: $CONTAINER_COUNT"
echo -e "${GREEN}Successfully cleaned: $CLEANED_COUNT${NC}"
if [[ $FAILED_COUNT -gt 0 ]]; then
  echo -e "${RED}Failed cleanup: $FAILED_COUNT${NC}"
  for agent in "${FAILED_AGENTS[@]}"; do
    echo -e "${RED}  - $agent${NC}"
  done
  echo ""
  exit 1
else
  echo -e "${GREEN}All sandboxes cleaned successfully${NC}"
  echo ""
  exit 0
fi
