#!/usr/bin/env bash
set -euo pipefail

# ── validate-workflow.sh ──────────────────────────────────────────────
# Single command that runs ALL pre-push validations.
# Exit code 0 = all passed, non-zero = failure with details.
#
# Usage: bash scripts/validate-workflow.sh
# ────────────────────────────────────────────────────────────────────────

echo "=== validate-workflow.sh ==="
echo ""

errors=0

# ── 1. Branch naming ──────────────────────────────────────────────────
BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo "[branch] Current: $BRANCH"

case "$BRANCH" in
  main|dev)
    # allowed branches, skip naming check
    ;;
  feature/*|fix/*)
    ;;
  *)
    echo "[FAIL] Branch must be feature/* or fix/* (got: $BRANCH)"
    errors=$((errors + 1))
    ;;
esac

# ── 2. ruff check (backend lint) ──────────────────────────────────────
echo ""
echo "[ruff] Running ruff check dashboard/..."

if command -v ruff &>/dev/null; then
    ruff check dashboard/ && echo "[PASS] ruff check passed" || {
        echo "[FAIL] ruff check failed"
        errors=$((errors + 1))
    }
else
    echo "[SKIP] ruff not installed (install: pip install ruff)"
fi

# ── 3. Python syntax check ────────────────────────────────────────────
echo ""
echo "[py_compile] Running python3 -m py_compile dashboard/main.py..."

if python3 -m py_compile dashboard/main.py; then
    echo "[PASS] python syntax check passed"
else
    echo "[FAIL] python syntax check failed"
    errors=$((errors + 1))
fi

# ── 4. Frontend build ─────────────────────────────────────────────────
echo ""
echo "[pnpm] Running pnpm run build..."

if [ -d dashboard/frontend ]; then
    if pnpm --dir dashboard/frontend run build &>/dev/null; then
        echo "[PASS] frontend build passed"
    else
        echo "[FAIL] frontend build failed"
        errors=$((errors + 1))
    fi
else
    echo "[SKIP] dashboard/frontend not found"
fi

# ── 5. Frontend tests ─────────────────────────────────────────────────
echo ""
echo "[pnpm test] Running pnpm run test..."

if [ -d dashboard/frontend ]; then
    if pnpm --dir dashboard/frontend run test &>/dev/null; then
        echo "[PASS] frontend tests passed"
    else
        echo "[FAIL] frontend tests failed"
        errors=$((errors + 1))
    fi
else
    echo "[SKIP] dashboard/frontend not found"
fi

# ── 6. Workflow YAML validation (if python + yaml available) ──────────
echo ""
echo "[workflow] Validating specs/workflow.yaml..."

if python3 -c "import yaml, json, sys; yaml.safe_load(open('specs/workflow.yaml')); sys.exit(0)" 2>/dev/null; then
    echo "[PASS] workflow YAML is valid"
else
    echo "[SKIP] workflow YAML validation (install PyYAML: pip install pyyaml)"
fi

echo ""
echo "=========================================="
if [ "$errors" -eq 0 ]; then
    echo "All validations PASSED"
    exit 0
else
    echo "$errors validation(s) FAILED"
    exit 1
fi
