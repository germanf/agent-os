#!/bin/bash

# parallel-test.sh - Test parallel execution of 3 agents simultaneously
# Tests port allocation, isolation, and concurrent execution
# All 3 agents (fullstack, qa, ui) start in parallel with no conflicts

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
PROJECT_ROOT="$(dirname "$SANDBOX_ROOT")"
TMP_DIR="$PROJECT_ROOT/tmp"

# Get working directory for worktree
WORKTREE_PATH="$(cd "$SANDBOX_ROOT/../.." && pwd)"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Parallel Sandbox Test${NC}"
echo -e "${BLUE}Testing 3 agents: fullstack, qa, ui${NC}"
echo -e "${BLUE}========================================${NC}"
echo "Working directory: $WORKTREE_PATH"
echo ""

# Agent IDs
FULLSTACK_AGENT="parallel-fullstack-001"
QA_AGENT="parallel-qa-001"
UI_AGENT="parallel-ui-001"

# Track results
TESTS_PASSED=0
TESTS_FAILED=0
FAILED_AGENTS=()

# Cleanup function (called on exit)
cleanup_all() {
  echo ""
  echo -e "${YELLOW}Performing cleanup...${NC}"

  for agent in "$FULLSTACK_AGENT" "$QA_AGENT" "$UI_AGENT"; do
    echo -e "${YELLOW}Stopping $agent...${NC}"
    "$SCRIPT_DIR/sandbox-down.sh" "$agent" > /dev/null 2>&1 || true
  done
}

trap cleanup_all EXIT

# Helper function to run test
run_test() {
  local test_name="$1"
  local test_command="$2"

  echo -n -e "${YELLOW}$test_name... ${NC}"

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

# Phase 1: Start all 3 agents in parallel
echo -e "${YELLOW}=== Phase 1: Parallel Agent Startup ===${NC}"
echo "Starting fullstack, qa, and ui agents simultaneously..."
echo ""

# Start all three in background and capture their PIDs
"$SCRIPT_DIR/sandbox-up.sh" fullstack "$WORKTREE_PATH" "$FULLSTACK_AGENT" > /tmp/fullstack-startup.log 2>&1 &
FULLSTACK_PID=$!

"$SCRIPT_DIR/sandbox-up.sh" qa "$WORKTREE_PATH" "$QA_AGENT" > /tmp/qa-startup.log 2>&1 &
QA_PID=$!

"$SCRIPT_DIR/sandbox-up.sh" ui "$WORKTREE_PATH" "$UI_AGENT" > /tmp/ui-startup.log 2>&1 &
UI_PID=$!

echo -e "${YELLOW}Started agents: fullstack (PID $FULLSTACK_PID), qa (PID $QA_PID), ui (PID $UI_PID)${NC}"
echo -e "${YELLOW}Waiting for all agents to start...${NC}"

# Wait for all to complete
if wait "$FULLSTACK_PID"; then
  echo -e "${GREEN}✓ Fullstack agent started${NC}"
  ((TESTS_PASSED++))
else
  echo -e "${RED}✗ Fullstack agent startup failed${NC}"
  FAILED_AGENTS+=("fullstack")
  ((TESTS_FAILED++))
fi

if wait "$QA_PID"; then
  echo -e "${GREEN}✓ QA agent started${NC}"
  ((TESTS_PASSED++))
else
  echo -e "${RED}✗ QA agent startup failed${NC}"
  FAILED_AGENTS+=("qa")
  ((TESTS_FAILED++))
fi

if wait "$UI_PID"; then
  echo -e "${GREEN}✓ UI agent started${NC}"
  ((TESTS_PASSED++))
else
  echo -e "${RED}✗ UI agent startup failed${NC}"
  FAILED_AGENTS+=("ui")
  ((TESTS_FAILED++))
fi

if [[ ${#FAILED_AGENTS[@]} -gt 0 ]]; then
  echo ""
  echo -e "${RED}Some agents failed to start. Cannot continue.${NC}"
  echo -e "${RED}Test Result: FAIL${NC}"
  exit 1
fi

echo ""

# Extract ports
FULLSTACK_PORT=$(grep -oP "127\.0\.0\.1:\K\d+" "$TMP_DIR/.docker-compose.${FULLSTACK_AGENT}.yml" | head -1)
QA_PORT=$(grep -oP "127\.0\.0\.1:\K\d+" "$TMP_DIR/.docker-compose.${QA_AGENT}.yml" | head -1)
UI_PORT=$(grep -oP "127\.0\.0\.1:\K\d+" "$TMP_DIR/.docker-compose.${UI_AGENT}.yml" | head -1)

echo -e "${GREEN}Ports assigned:${NC}"
echo -e "${GREEN}  Fullstack: $FULLSTACK_PORT (8800-8849)${NC}"
echo -e "${GREEN}  QA: $QA_PORT (8850-8899)${NC}"
echo -e "${GREEN}  UI: $UI_PORT (8900-8949)${NC}"
echo ""

# Phase 2: Verify all agents running simultaneously
echo -e "${YELLOW}=== Phase 2: Concurrent Execution ===${NC}"

run_test "Fullstack container running" \
  "docker ps --filter 'name=claude-sandbox-$FULLSTACK_AGENT' | grep -q 'claude-sandbox-$FULLSTACK_AGENT'"

run_test "QA container running" \
  "docker ps --filter 'name=claude-sandbox-$QA_AGENT' | grep -q 'claude-sandbox-$QA_AGENT'"

run_test "UI container running" \
  "docker ps --filter 'name=claude-sandbox-$UI_AGENT' | grep -q 'claude-sandbox-$UI_AGENT'"

echo ""

# Phase 3: Port collision detection
echo -e "${YELLOW}=== Phase 3: Port Collision Detection ===${NC}"

# Verify ports are different
if [[ "$FULLSTACK_PORT" == "$QA_PORT" ]] || [[ "$FULLSTACK_PORT" == "$UI_PORT" ]] || [[ "$QA_PORT" == "$UI_PORT" ]]; then
  echo -e "${RED}✗ Port collision detected!${NC}"
  echo -e "${RED}  Fullstack: $FULLSTACK_PORT${NC}"
  echo -e "${RED}  QA: $QA_PORT${NC}"
  echo -e "${RED}  UI: $UI_PORT${NC}"
  ((TESTS_FAILED++))
else
  echo -e "${GREEN}✓ No port collisions (all unique)${NC}"
  ((TESTS_PASSED++))
fi

# Verify port ranges
FULLSTACK_RANGE_OK=0
if [[ $FULLSTACK_PORT -ge 8800 && $FULLSTACK_PORT -le 8849 ]]; then
  FULLSTACK_RANGE_OK=1
  echo -e "${GREEN}✓ Fullstack port in range (8800-8849)${NC}"
  ((TESTS_PASSED++))
else
  echo -e "${RED}✗ Fullstack port out of range${NC}"
  ((TESTS_FAILED++))
fi

QA_RANGE_OK=0
if [[ $QA_PORT -ge 8850 && $QA_PORT -le 8899 ]]; then
  QA_RANGE_OK=1
  echo -e "${GREEN}✓ QA port in range (8850-8899)${NC}"
  ((TESTS_PASSED++))
else
  echo -e "${RED}✗ QA port out of range${NC}"
  ((TESTS_FAILED++))
fi

UI_RANGE_OK=0
if [[ $UI_PORT -ge 8900 && $UI_PORT -le 8949 ]]; then
  UI_RANGE_OK=1
  echo -e "${GREEN}✓ UI port in range (8900-8949)${NC}"
  ((TESTS_PASSED++))
else
  echo -e "${RED}✗ UI port out of range${NC}"
  ((TESTS_FAILED++))
fi

echo ""

# Phase 4: CI checks for all agents
echo -e "${YELLOW}=== Phase 4: CI Checks (All Agents) ===${NC}"

run_test "Fullstack CI checks" \
  "docker exec claude-sandbox-$FULLSTACK_AGENT bash /app/sandbox/scripts/ci-checks.sh > /dev/null 2>&1"

run_test "QA CI checks" \
  "docker exec claude-sandbox-$QA_AGENT bash /app/sandbox/scripts/ci-checks.sh > /dev/null 2>&1"

run_test "UI CI checks" \
  "docker exec claude-sandbox-$UI_AGENT bash /app/sandbox/scripts/ci-checks.sh > /dev/null 2>&1"

echo ""

# Phase 5: Volume isolation
echo -e "${YELLOW}=== Phase 5: Volume Isolation ===${NC}"

run_test "Each agent has unique venv volume" \
  "[[ $(docker volume ls --format '{{.Name}}' | grep '^venv-parallel' | wc -l) -eq 3 ]]"

run_test "Each agent has unique node_modules volume" \
  "[[ $(docker volume ls --format '{{.Name}}' | grep '^node-modules-parallel' | wc -l) -eq 3 ]]"

echo ""

# Phase 6: Graceful shutdown in correct order
echo -e "${YELLOW}=== Phase 6: Graceful Shutdown ===${NC}"
echo "Shutting down all agents..."
echo ""

# Note: cleanup_all() will be called by trap on exit
# But we can manually verify the cleanup process here

# Summary
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Parallel Test Summary${NC}"
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
  echo -e "${GREEN}All agents ran successfully in parallel${NC}"
  echo -e "${GREEN}Port allocation: ✓ No collisions${NC}"
  echo -e "${GREEN}Volume isolation: ✓ Complete${NC}"
  echo -e "${GREEN}CI validation: ✓ All passed${NC}"
  echo ""
  echo -e "${GREEN}Test Result: PASS${NC}"
  echo ""
  exit 0
fi
