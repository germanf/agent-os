#!/bin/bash
# check-sandboxes.sh — Alert on orphan Docker containers
#
# Checks for containers running without their worktree (or stale entries).
# Requires sandbox-up.sh and sandbox-down.sh to maintain sandbox/.running.
#
# Usage: ./check-sandboxes.sh
#
# Exit codes:
#   0 = no alerts (all sandboxes OK or no active sandboxes)
#   1 = alerts found (ALERT printed)

set -o pipefail

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
RUNNING_FILE="$PROJECT_ROOT/sandbox/.running"

ALERTS_FOUND=0

# Check if Docker is available
if ! command -v docker >/dev/null 2>&1; then
  echo -e "${BLUE}ℹ${NC}   Docker not available, skipping sandbox check"
  exit 0
fi

# Check if .running file exists
if [[ ! -f "$RUNNING_FILE" ]]; then
  echo -e "${BLUE}ℹ${NC}   No active sandboxes tracked"
  exit 0
fi

# If .running exists but is empty, no active sandboxes
if [[ ! -s "$RUNNING_FILE" ]]; then
  echo -e "${BLUE}ℹ${NC}   No active sandboxes tracked"
  exit 0
fi

# Temporary file for updated .running entries
TEMP_RUNNING=$(mktemp)
trap "rm -f $TEMP_RUNNING" EXIT

# Process each line in .running
# Format: <agent-id> <container-name> <worktree-path> <timestamp-epoch>
while IFS= read -r line; do
  if [[ -z "$line" ]]; then
    continue
  fi

  # Parse the line
  read -r agent_id container_name worktree_path timestamp <<< "$line"

  if [[ -z "$agent_id" ]] || [[ -z "$container_name" ]]; then
    # Malformed line, skip silently
    continue
  fi

  # Check if container is running
  CONTAINER_EXISTS=$(docker ps --filter "name=$container_name" --format "{{.Names}}" 2>/dev/null | grep -q "^${container_name}$" && echo "yes" || echo "no")

  # Check if worktree path exists
  WORKTREE_EXISTS=$([ -d "$worktree_path" ] && echo "yes" || echo "no")

  if [[ "$CONTAINER_EXISTS" == "yes" ]] && [[ "$WORKTREE_EXISTS" == "yes" ]]; then
    # Both exist — OK
    echo -e "${GREEN}✅${NC}  OK: $container_name (worktree: $worktree_path)"
    echo "$line" >> "$TEMP_RUNNING"

  elif [[ "$CONTAINER_EXISTS" == "yes" ]] && [[ "$WORKTREE_EXISTS" == "no" ]]; then
    # Container running but worktree missing — orphan
    echo -e "${RED}❌${NC}  ALERT: $container_name — container running but worktree $worktree_path MISSING"
    echo "   Run: ./sandbox/scripts/sandbox-down.sh $agent_id to clean up orphan container"
    ALERTS_FOUND=1
    # Do NOT add to new .running (container is orphaned)

  elif [[ "$CONTAINER_EXISTS" == "no" ]] && [[ "$WORKTREE_EXISTS" == "yes" ]]; then
    # Container stopped but entry still exists — stale
    echo -e "${YELLOW}⚠️${NC}  Stale entry: $agent_id (container not running, worktree still exists)"
    # Remove from .running (entry is stale)

  else
    # Container stopped and worktree gone — cleanup silently
    # Entry is stale and safe to remove
    :
  fi

done < "$RUNNING_FILE"

# Replace .running with cleaned-up version
if [[ -s "$TEMP_RUNNING" ]]; then
  cat "$TEMP_RUNNING" > "$RUNNING_FILE"
else
  # No active entries left, remove the file
  rm -f "$RUNNING_FILE"
fi

exit $ALERTS_FOUND
