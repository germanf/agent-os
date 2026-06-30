#!/bin/bash
# check-worktrees.sh — Alert on potentially abandoned worktrees
#
# Checks for worktrees that look abandoned (no PR open, older than threshold).
#
# Usage: ./check-worktrees.sh
#
# Exit codes:
#   0 = no alerts (all worktrees OK or no non-main worktrees)
#   1 = alerts found (WARNING or ALERT printed)

set -o pipefail

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Threshold ages (in seconds)
WARNING_THRESHOLD=$((4 * 3600))    # 4 hours
ALERT_THRESHOLD=$((24 * 3600))     # 24 hours

ALERTS_FOUND=0

# Get current timestamp
NOW=$(date +%s)

# Get list of all worktrees in porcelain format
# Porcelain format is multi-line per worktree:
# worktree /path/to/worktree
# HEAD <commit-hash>
# branch refs/heads/branch-name
# [detached]|[locked]|[prunable]
#
# We parse this by reading "worktree" lines as markers for new entries.
WORKTREES=$(git worktree list --porcelain 2>/dev/null || true)

if [[ -z "$WORKTREES" ]]; then
  echo -e "${BLUE}ℹ${NC}   No worktrees found"
  exit 0
fi

# Find the main worktree (the one at the repo root)
MAIN_WORKTREE="$(git rev-parse --show-toplevel 2>/dev/null)"

# Parse porcelain output and extract worktrees
# Store as: path|branch (pipe-separated)
declare -a WORKTREE_LIST

current_path=""
current_branch=""

while IFS= read -r line; do
  if [[ -z "$line" ]]; then
    continue
  fi

  if [[ "$line" =~ ^worktree[[:space:]]+ ]]; then
    # Save previous worktree if we have one
    if [[ -n "$current_path" ]]; then
      WORKTREE_LIST+=("$current_path|$current_branch")
    fi
    # Extract path
    current_path="${line#worktree }"
    current_branch=""

  elif [[ "$line" =~ ^branch[[:space:]]+ ]]; then
    # Extract branch (may include refs/heads/)
    current_branch="${line#branch }"

  fi
done <<< "$WORKTREES"

# Don't forget the last one
if [[ -n "$current_path" ]]; then
  WORKTREE_LIST+=("$current_path|$current_branch")
fi

# Process each worktree
for entry in "${WORKTREE_LIST[@]}"; do
  path="${entry%|*}"
  branch="${entry#*|}"

  # Skip the main worktree
  if [[ "$path" == "$MAIN_WORKTREE" ]]; then
    continue
  fi

  # Strip "refs/heads/" prefix from branch if present
  branch="${branch#refs/heads/}"

  # Check if worktree path still exists
  if [[ ! -d "$path" ]]; then
    echo -e "${YELLOW}⚠️${NC}  Stale entry: $branch (worktree path missing: $path)"
    ALERTS_FOUND=1
    continue
  fi

  # Get age of last commit in this worktree
  COMMIT_TIMESTAMP=$(git -C "$path" log -1 --format="%ct" 2>/dev/null || echo "0")

  if [[ "$COMMIT_TIMESTAMP" == "0" ]]; then
    echo -e "${YELLOW}⚠️${NC}  $branch — could not determine commit age (worktree: $path)"
    continue
  fi

  AGE_SECONDS=$((NOW - COMMIT_TIMESTAMP))
  AGE_HOURS=$((AGE_SECONDS / 3600))

  # Check for open PR
  GH_STATUS=0
  OPEN_PR=$(command -v gh >/dev/null 2>&1 && gh pr list --head "$branch" --state open --json number --jq 'length' 2>/dev/null) || GH_STATUS=$?

  if [[ $GH_STATUS != 0 ]]; then
    # gh failed or not available, report without PR check but still flag age
    if [[ $AGE_SECONDS -gt $ALERT_THRESHOLD ]]; then
      echo -e "${RED}❌${NC}  ALERT: $branch — ${AGE_HOURS}h old, could not verify PR status (gh unavailable)"
      echo "   Run: git worktree list to inspect, git worktree remove --force $path if confirmed abandoned"
      ALERTS_FOUND=1
    elif [[ $AGE_SECONDS -gt $WARNING_THRESHOLD ]]; then
      echo -e "${YELLOW}⚠️${NC}  WARNING: $branch — ${AGE_HOURS}h old, could not verify PR status (gh unavailable)"
      echo "   Run: git worktree list to inspect, git worktree remove --force $path if confirmed abandoned"
      ALERTS_FOUND=1
    fi
    continue
  fi

  # Categorize by age and PR status
  if [[ "$OPEN_PR" != "0" ]]; then
    # Has an open PR — not abandoned
    echo -e "${GREEN}✅${NC}  OK: $branch — open PR #$OPEN_PR"
  elif [[ $AGE_SECONDS -gt $ALERT_THRESHOLD ]]; then
    # No PR and older than 24h — alert
    echo -e "${RED}❌${NC}  ALERT: $branch — ${AGE_HOURS}h old, no open PR — likely abandoned, CTO must review"
    echo "   Worktree: $path"
    ALERTS_FOUND=1
  elif [[ $AGE_SECONDS -gt $WARNING_THRESHOLD ]]; then
    # No PR and older than 4h — warning
    echo -e "${YELLOW}⚠️${NC}  WARNING: $branch — ${AGE_HOURS}h old, no open PR (worktree: $path)"
    echo "   Run: git worktree list to inspect, git worktree remove --force $path if confirmed abandoned"
    ALERTS_FOUND=1
  else
    # Recent and no PR — OK (still building)
    echo -e "${GREEN}✅${NC}  OK: $branch — recent, no PR yet (${AGE_HOURS}h old)"
  fi

done

# Check if we found any non-main worktrees at all
NON_MAIN_COUNT=0
for entry in "${WORKTREE_LIST[@]}"; do
  path="${entry%|*}"
  if [[ "$path" != "$MAIN_WORKTREE" ]]; then
    NON_MAIN_COUNT=$((NON_MAIN_COUNT + 1))
  fi
done

if [[ $NON_MAIN_COUNT -eq 0 ]] && [[ $ALERTS_FOUND -eq 0 ]]; then
  echo -e "${BLUE}ℹ${NC}   No non-main worktrees found"
fi

exit $ALERTS_FOUND
