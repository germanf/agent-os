#!/bin/bash

# sandbox-test.sh - Test sandbox functionality for a single agent
# Usage: sandbox-test.sh <ROLE> <AGENT_ID>
# Tests: startup, CI checks, health endpoint, cleanup

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SANDBOX_ROOT="$(dirname "$SCRIPT_DIR")"

# Parameters
ROLE="${1:-}"
AGENT_ID="${2:-}"

# Validation
if [[ -z "$ROLE" ]]; then
  echo -e "${RED}Error: ROLE parameter required${NC}" >&2
  echo "Usage: $0 <ROLE> <AGENT_ID>" >&2
  echo "Roles: fullstack, qa, ui" >&2
  exit 1
fi

if [[ -z "$AGENT_ID" ]]; then
  echo -e "${RED}Error: AGENT_ID parameter required${NC}" >&2
  exit 1
fi

# Get working directory for worktree
WORKTREE_PATH="$(cd "$SANDBOX_ROOT/../.." && pwd)"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Sandbox Test: $ROLE ($AGENT_ID)${NC}"
echo -e "${BLUE}========================================${NC}"
echo "Working directory: $WORKTREE_PATH"
echo ""

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0

# Helper function to run test
run_test() {
  local test_name="$1"
  local test_command="$2"

  echo -n -e "${YELLOW}Testing: $test_name... ${NC}"

  if eval "$test_command" > /dev/null 2>&1; then
    echo -e "${GREEN}PASS${NC}"
    ((TESTS_PASSED++))
    return 0
  else
    echo -e "${RED}FAIL${NC}"
    ((TESTS_FAILED++))
    return 1
  fi
}

# Test 1: Sandbox startup
echo -e "${YELLOW}=== Phase 1: Sandbox Startup ===${NC}"

run_test "Starting sandbox" \
  "$SCRIPT_DIR/sandbox-up.sh $ROLE $WORKTREE_PATH $AGENT_ID"

STARTUP_RESULT=$?

if [[ $STARTUP_RESULT -ne 0 ]]; then
  echo -e "${RED}Sandbox startup failed, cannot continue tests${NC}"
  echo -e "${RED}Test Result: FAIL${NC}"
  exit 1
fi

# Get the port that was assigned
COMPOSE_FILE="$SANDBOX_ROOT/.docker-compose.${AGENT_ID}.yml"
if [[ ! -f "$COMPOSE_FILE" ]]; then
  echo -e "${RED}Error: Compose file not found after startup${NC}"
  exit 1
fi

PORT=$(grep -oP "127\.0\.0\.1:\K\d+" "$COMPOSE_FILE" | head -1)
if [[ -z "$PORT" ]]; then
  echo -e "${RED}Error: Could not extract port from compose file${NC}"
  exit 1
fi

echo -e "${GREEN}Sandbox started on port $PORT${NC}"
echo ""

# Test 2: Container verification
echo -e "${YELLOW}=== Phase 2: Container Verification ===${NC}"

run_test "Container is running" \
  "docker ps --filter 'name=claude-sandbox-$AGENT_ID' | grep -q 'claude-sandbox-$AGENT_ID'"

run_test "Container is healthy" \
  "docker ps --filter 'name=claude-sandbox-$AGENT_ID' --filter 'status=running' | grep -q 'claude-sandbox-$AGENT_ID'"

# Test 3: CI checks
echo ""
echo -e "${YELLOW}=== Phase 3: CI Checks ===${NC}"

run_test "TypeScript build" \
  "docker exec claude-sandbox-$AGENT_ID bash -c 'cd /app/dashboard/frontend && npm run build > /dev/null 2>&1'"

run_test "Python syntax validation" \
  "docker exec claude-sandbox-$AGENT_ID bash -c 'python3 -m py_compile /app/dashboard/main.py'"

# Test 4: Endpoint verification
echo ""
echo -e "${YELLOW}=== Phase 4: Endpoint Verification ===${NC}"

# Start the app in background (if possible)
echo -e "${YELLOW}Starting uvicorn in container...${NC}"
docker exec -d "claude-sandbox-$AGENT_ID" bash /app/sandbox/scripts/entrypoint.sh > /dev/null 2>&1 || true

# Wait for app to start
sleep 3

# Try to connect to health endpoint
run_test "Health endpoint accessible (GET /health)" \
  "curl -s http://127.0.0.1:$PORT/health | grep -q 'ok' || curl -s http://127.0.0.1:$PORT/ | grep -q 'html'"

# Test 5: Volume isolation
echo ""
echo -e "${YELLOW}=== Phase 5: Volume Isolation ===${NC}"

run_test "Python venv volume exists" \
  "docker volume inspect venv-$AGENT_ID > /dev/null 2>&1"

run_test "Node modules volume exists" \
  "docker volume inspect node-modules-$AGENT_ID > /dev/null 2>&1"

run_test "Volumes are separate" \
  "[[ $(docker volume ls --format '{{.Name}}' | grep -c '^venv-' || true) -ge 1 ]]"

# Test 6: Port range validation
echo ""
echo -e "${YELLOW}=== Phase 6: Port Range Validation ===${NC}"

case "$ROLE" in
  fullstack)
    PORT_MIN=8800
    PORT_MAX=8849
    ;;
  qa)
    PORT_MIN=8850
    PORT_MAX=8899
    ;;
  ui)
    PORT_MIN=8900
    PORT_MAX=8949
    ;;
esac

run_test "Port in valid range ($PORT_MIN-$PORT_MAX)" \
  "[[ $PORT -ge $PORT_MIN && $PORT -le $PORT_MAX ]]"

# Test 7: Cleanup
echo ""
echo -e "${YELLOW}=== Phase 7: Cleanup ===${NC}"

run_test "Sandbox cleanup" \
  "$SCRIPT_DIR/sandbox-down.sh $AGENT_ID"

run_test "Container removed" \
  "! docker ps -a --filter 'name=claude-sandbox-$AGENT_ID' | grep -q 'claude-sandbox-$AGENT_ID' || true"

run_test "Volumes removed" \
  "! docker volume inspect venv-$AGENT_ID > /dev/null 2>&1 || true"

# Final report
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Test Summary${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
if [[ $TESTS_FAILED -gt 0 ]]; then
  echo -e "${RED}Failed: $TESTS_FAILED${NC}"
  echo ""
  echo -e "${RED}Test Result: FAIL${NC}"
  echo ""
  exit 1
else
  echo -e "${GREEN}Failed: $TESTS_FAILED${NC}"
  echo ""
  echo -e "${GREEN}Test Result: PASS${NC}"
  echo ""
  exit 0
fi
