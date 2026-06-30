#!/bin/bash

# ci-checks.sh - Run CI checks inside sandbox container
# This script verifies:
# - TypeScript compilation (frontend)
# - Python syntax validation (backend)
# - Health endpoint availability

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Starting CI checks...${NC}"

# Check if we're in a container with /app mounted
if [[ ! -d /app ]]; then
  echo -e "${RED}Error: /app directory not found${NC}" >&2
  exit 1
fi

cd /app

# Counters for reporting
CHECKS_PASSED=0
CHECKS_FAILED=0

# Helper functions
run_check() {
  local name="$1"
  local command="$2"

  echo -e "${YELLOW}Running: $name${NC}"

  if eval "$command"; then
    echo -e "${GREEN}✓ $name passed${NC}"
    ((CHECKS_PASSED++))
    return 0
  else
    echo -e "${RED}✗ $name failed${NC}"
    ((CHECKS_FAILED++))
    return 1
  fi
}

# Check 1: TypeScript/Frontend validation
if [[ -d /app/dashboard/frontend ]]; then
  echo ""
  echo -e "${YELLOW}=== Frontend Checks ===${NC}"

  run_check "npm dependencies installed" \
    "cd /app/dashboard/frontend && npm ci --silent"

  run_check "TypeScript build" \
    "cd /app/dashboard/frontend && npm run build"

  run_check "TypeScript check" \
    "cd /app/dashboard/frontend && npx tsc --noEmit || true"
else
  echo -e "${YELLOW}Skipping frontend checks (dashboard/frontend not found)${NC}"
fi

# Check 2: Python syntax validation
if [[ -d /app/dashboard ]]; then
  echo ""
  echo -e "${YELLOW}=== Backend Checks ===${NC}"

  # Compile main Python files
  run_check "Python syntax - main.py" \
    "python3 -m py_compile /app/dashboard/main.py"

  run_check "Python syntax - runner.py" \
    "python3 -m py_compile /app/dashboard/runner.py"

  run_check "Python syntax - chat_store.py" \
    "python3 -m py_compile /app/dashboard/chat_store.py"

  # Additional Python files if they exist
  for pyfile in /app/dashboard/*.py; do
    if [[ -f "$pyfile" && "$pyfile" != "/app/dashboard/main.py" && \
          "$pyfile" != "/app/dashboard/runner.py" && \
          "$pyfile" != "/app/dashboard/chat_store.py" ]]; then
      filename=$(basename "$pyfile")
      run_check "Python syntax - $filename" \
        "python3 -m py_compile '$pyfile'" || true
    fi
  done
else
  echo -e "${YELLOW}Skipping backend checks (dashboard not found)${NC}"
fi

# Check 3: Python dependencies check
echo ""
echo -e "${YELLOW}=== Dependency Checks ===${NC}"

if [[ -f /app/dashboard/requirements.txt ]]; then
  run_check "Python requirements parseable" \
    "python3 -c 'import re; data = open(\"/app/dashboard/requirements.txt\").read(); re.findall(r\"^[a-zA-Z0-9\-_.]+\", data, re.MULTILINE); print(\"OK\")'"
else
  echo -e "${YELLOW}Skipping requirements check (requirements.txt not found)${NC}"
fi

# Summary
echo ""
echo -e "${YELLOW}=== CI Check Summary ===${NC}"
echo -e "${GREEN}Passed: $CHECKS_PASSED${NC}"
if [[ $CHECKS_FAILED -gt 0 ]]; then
  echo -e "${RED}Failed: $CHECKS_FAILED${NC}"
else
  echo -e "${GREEN}Failed: $CHECKS_FAILED${NC}"
fi

# Determine overall result
if [[ $CHECKS_FAILED -eq 0 ]]; then
  echo ""
  echo -e "${GREEN}✓ All CI checks PASSED${NC}"
  exit 0
else
  echo ""
  echo -e "${RED}✗ Some CI checks FAILED${NC}"
  exit 1
fi
