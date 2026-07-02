#!/bin/bash

# sandbox-cleanup.sh - Tear down sandbox after successful tests + PR merge
# Usage: sandbox-cleanup.sh <AGENT_ID> [PR_NUMBER]
#
# If PR_NUMBER is given, verifies the PR is merged to dev before cleanup.
# Without PR_NUMBER, cleans up immediately.

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENT_ID="${1:-}"
PR_NUMBER="${2:-}"

if [[ -z "$AGENT_ID" ]]; then
  echo -e "${RED}Usage: $0 <AGENT_ID> [PR_NUMBER]${NC}" >&2
  exit 1
fi

# If PR number provided, verify it is merged to dev before cleanup
if [[ -n "$PR_NUMBER" ]]; then
  echo -e "${YELLOW}Checking PR #$PR_NUMBER merge status...${NC}"

  if ! command -v gh &>/dev/null; then
    echo -e "${RED}gh CLI not found — cannot verify PR merge status. Aborting.${NC}" >&2
    exit 1
  fi

  PR_JSON=$(gh pr view "$PR_NUMBER" --json state,merged,baseRefName 2>/dev/null || true)

  if [[ -z "$PR_JSON" ]]; then
    echo -e "${RED}PR #$PR_NUMBER not found.${NC}" >&2
    exit 1
  fi

  STATE=$(echo "$PR_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin).get('state',''))" 2>/dev/null || echo "")
  MERGED=$(echo "$PR_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin).get('merged',False))" 2>/dev/null || echo "False")
  BASE=$(echo "$PR_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin).get('baseRefName',''))" 2>/dev/null || echo "")

  if [[ "$STATE" != "MERGED" ]] || [[ "$MERGED" != "True" ]]; then
    echo -e "${YELLOW}PR #$PR_NUMBER is not merged yet (state=$STATE, merged=$MERGED). Cleanup deferred.${NC}"
    exit 0
  fi

  if [[ "$BASE" != "dev" ]]; then
    echo -e "${YELLOW}PR #$PR_NUMBER targets '$BASE', not 'dev'. Cleanup deferred.${NC}"
    exit 0
  fi

  echo -e "${GREEN}PR #$PR_NUMBER is merged to dev. Proceeding with cleanup.${NC}"
fi

echo -e "${YELLOW}Cleaning up sandbox for agent: $AGENT_ID${NC}"
"$SCRIPT_DIR/sandbox-down.sh" "$AGENT_ID"
echo -e "${GREEN}Cleanup complete for agent $AGENT_ID${NC}"
