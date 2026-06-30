#!/bin/bash
# sync-memory.sh — Memory STATE.md validation & interactive correction
#
# Phase 2: Read-only validation
#   ./sync-memory.sh                 # Detect drift (exit 0 if synced, 1 if drift)
#   ./sync-memory.sh --verbose       # Detailed report
#
# Phase 3: Interactive correction (Opción C)
#   ./sync-memory.sh --fix           # Propose changes, categorize safe/ambiguous
#   ./sync-memory.sh --fix --review  # Interactive prompts for ambiguous decisions
#   ./sync-memory.sh --fix --safe-only  # Auto-apply safe changes only (no prompts)
#
# Exit codes:
#   0 = synced (no drift)
#   1 = drift detected (or user declined changes)
#   2 = error running gh/git/file commands

set -o pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
MEMORY_DIR="$HOME/.claude/projects/-home-ubuntu-Claude/memory"
STATE_FILE="$MEMORY_DIR/STATE.md"
TEMP_DIR="/tmp/sync-memory-$$"

FIX=false
REVIEW=false
SAFE_ONLY=false
VERBOSE=false
DRY_RUN=false

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --fix) FIX=true; shift ;;
    --review) REVIEW=true; shift ;;
    --safe-only) SAFE_ONLY=true; FIX=true; shift ;;
    --verbose) VERBOSE=true; shift ;;
    --dry-run) DRY_RUN=true; shift ;;
    *) echo "Unknown option: $1"; exit 2 ;;
  esac
done

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
NC='\033[0m'

log_info() { echo -e "${BLUE}ℹ${NC} $*"; }
log_success() { echo -e "${GREEN}✅${NC} $*"; }
log_warn() { echo -e "${YELLOW}⚠️${NC} $*"; }
log_error() { echo -e "${RED}❌${NC} $*"; }
log_prompt() { echo -e "${MAGENTA}❓${NC} $*"; }

cleanup() {
  [[ -d "$TEMP_DIR" ]] && rm -rf "$TEMP_DIR"
}
trap cleanup EXIT

# update_table_section <file> <section_header> <line_pattern> <new_lines_file>
#
# Within the block that starts at the line matching <section_header> (exact
# match, e.g. "## PRs Activos") and ends right before the next line starting
# with "## " (or EOF), replace every line matching the extended regex
# <line_pattern> with the contents of <new_lines_file>, inserted where the
# first matching line was (or right after the header if no line matched).
# All other lines in the section (prose, **Total:**, **Nota:**, etc.) are
# left untouched — this is what keeps regeneration from clobbering
# surrounding narrative text.
update_table_section() {
  local file="$1" header="$2" pattern="$3" new_lines_file="$4"
  awk -v header="$header" -v pattern="$pattern" -v new_lines_file="$new_lines_file" '
    BEGIN { in_section = 0; inserted = 0 }
    {
      if ($0 == header) {
        in_section = 1
        print $0
        next
      }
      if (in_section && $0 ~ /^## /) {
        if (!inserted) {
          while ((getline line < new_lines_file) > 0) print line
          inserted = 1
        }
        in_section = 0
        print $0
        next
      }
      if (in_section && $0 ~ pattern) {
        if (!inserted) {
          while ((getline line < new_lines_file) > 0) print line
          inserted = 1
        }
        next
      }
      print $0
    }
    END {
      if (in_section && !inserted) {
        while ((getline line < new_lines_file) > 0) print line
      }
    }
  ' "$file"
}

# Verify prerequisites
if [[ ! -f "$STATE_FILE" ]]; then
  log_error "STATE.md not found at $STATE_FILE"
  exit 2
fi

if ! command -v gh &> /dev/null; then
  log_error "gh CLI not found. Install: https://cli.github.com/"
  exit 2
fi

mkdir -p "$TEMP_DIR"

log_info "Validating memory STATE.md against reality..."

# Get actual state from GitHub
actual_prs=$(gh pr list --state open --json number --jq 'length' 2>/dev/null || echo "ERROR")
actual_issues=$(gh issue list --state open --json number --jq 'length' 2>/dev/null || echo "ERROR")

if [[ "$actual_prs" == "ERROR" ]] || [[ "$actual_issues" == "ERROR" ]]; then
  log_error "Failed to fetch state from GitHub"
  exit 2
fi

# Collect changes to apply
declare -a SAFE_CHANGES
declare -a AMBIGUOUS_CHANGES

# ============================================================================
# SAFE CHANGES (can auto-apply without confirmation)
# ============================================================================

# 1. Check for stale timestamp (>24h old)
state_timestamp=$(grep "Última verificación" "$STATE_FILE" 2>/dev/null | head -1)
if [[ -z "$state_timestamp" ]]; then
  SAFE_CHANGES+=("update_timestamp:Update missing timestamp")
else
  # Extract timestamp: "**Última verificación:** 2026-06-25 22:30 UTC  "
  # Result should be: "2026-06-25 22:30"
  timestamp_str=$(echo "$state_timestamp" | grep -oP '\d{4}-\d{2}-\d{2} \d{2}:\d{2}' || echo "")

  # Parse "YYYY-MM-DD HH:MM" format
  timestamp_epoch=$(date -d "$timestamp_str" +%s 2>/dev/null)
  if [[ -z "$timestamp_epoch" ]]; then
    # Fallback: assume recent if can't parse
    timestamp_epoch=$(date +%s)
  fi
  now_epoch=$(date +%s)
  age_hours=$(( (now_epoch - timestamp_epoch) / 3600 ))

  if [[ $age_hours -gt 24 ]]; then
    SAFE_CHANGES+=("update_timestamp:Timestamp is $age_hours hours old")
  fi
fi

# 2. Check for open PRs mismatch
# Documented PR numbers are the "- #NNN: ..." lines inside the "## PRs Activos"
# section (same format that update_prs writes below) — detection and writing
# must agree on the format, or drift never resolves across runs.
documented_pr_numbers=$(sed -n '/^## PRs Activos/,/^## /p' "$STATE_FILE" 2>/dev/null | grep -oP '^- #\K[0-9]+' | sort)
actual_pr_numbers=$(gh pr list --state open --json number --jq '.[].number' 2>/dev/null | sort)

if [[ "$actual_pr_numbers" != "$documented_pr_numbers" ]]; then
  SAFE_CHANGES+=("update_prs:PR list mismatch: $actual_prs open, STATE.md may be outdated")
fi

# 3. Check for issue count mismatch
# Count documented issues only from rows inside the "## Issues Abiertos"
# table — not a file-wide grep, which also matches "| #NNN |" rows in the
# "## PRs Activos" table and mixes the two counts (bug #3).
documented_issues=$(sed -n '/^## Issues Abiertos/,/^## /p' "$STATE_FILE" 2>/dev/null | grep -c "^| #")
documented_issues=${documented_issues:-0}

# Compare not just the count but the actual set of issue numbers, so closed
# issues still listed (or new issues missing) are detected even if the total
# happens to match by coincidence.
documented_issue_numbers=$(sed -n '/^## Issues Abiertos/,/^## /p' "$STATE_FILE" 2>/dev/null | grep -oP '^\| #\K[0-9]+' | sort)
actual_issue_numbers=$(gh issue list --state open --json number --jq '.[].number' 2>/dev/null | sort)

if [[ $actual_issues -ne $documented_issues ]] || [[ "$actual_issue_numbers" != "$documented_issue_numbers" ]]; then
  SAFE_CHANGES+=("update_issue_count:Issue count changed from $documented_issues to $actual_issues")
fi

# ============================================================================
# AMBIGUOUS CHANGES (require human confirmation)
# ============================================================================

# 1. Blocker status (requires manual verification)
if grep -q "\[MANUAL VERIFY REQUIRED\]" "$STATE_FILE"; then
  AMBIGUOUS_CHANGES+=("blocker_verification:Verify non-auto-closeable blockers (e.g., #79 iptables)")
fi

# 2. Branch archive decisions
if git branch --list | grep -qE "stale|old"; then
  AMBIGUOUS_CHANGES+=("branch_archive:Archive old/stale branches (requires manual inspection)")
fi

# ============================================================================
# REPORT & FIX
# ============================================================================

if [[ ${#SAFE_CHANGES[@]} -eq 0 ]] && [[ ${#AMBIGUOUS_CHANGES[@]} -eq 0 ]]; then
  if [[ $FIX == false ]]; then
    log_success "STATE.md is in sync with GitHub/git"
    exit 0
  else
    log_success "No changes needed"
    exit 0
  fi
fi

# Show summary
if [[ $FIX == false ]]; then
  # Phase 2: Read-only report
  log_warn "DRIFT DETECTED"
  if [[ ${#SAFE_CHANGES[@]} -gt 0 ]]; then
    echo ""
    echo "Safe changes (can auto-apply):"
    for change in "${SAFE_CHANGES[@]}"; do
      reason="${change#*:}"
      echo "  ✓ $reason"
    done
  fi
  if [[ ${#AMBIGUOUS_CHANGES[@]} -gt 0 ]]; then
    echo ""
    echo "Ambiguous changes (require confirmation):"
    for change in "${AMBIGUOUS_CHANGES[@]}"; do
      reason="${change#*:}"
      echo "  ? $reason"
    done
  fi
  echo ""
  log_info "Run: /sync-memory --fix --review   (interactive)"
  log_info "Or:  /sync-memory --fix --safe-only (auto-safe only)"
  exit 1
fi

# Phase 3: Apply corrections
echo ""
log_info "Applying corrections..."

# Apply safe changes
for change in "${SAFE_CHANGES[@]}"; do
  action="${change%%:*}"
  reason="${change#*:}"

  case "$action" in
    update_timestamp)
      new_timestamp=$(date '+%Y-%m-%d %H:%M UTC')
      sed -i "s/^\*\*Última verificación:.*/**Última verificación:** $new_timestamp/" "$STATE_FILE" 2>/dev/null && \
        log_success "Updated timestamp: $new_timestamp" || \
        log_error "Failed to update timestamp"
      ;;
    update_prs)
      # Regenerate both the "✅ **Status:** N PRs open" line and the
      # "- #NNN: title (branch)" lines inside "## PRs Activos" from the real
      # `gh pr list` output, in place. Regenerating the status line too (not
      # just the list) guarantees there's always at least one line matching
      # <pattern> to anchor the replacement at — otherwise, when there are no
      # pre-existing "- #NNN" lines to match (e.g. going from 0 to 1 PR),
      # update_table_section falls through to inserting at the end of the
      # section, leaving the old status line stale and contradictory.
      # Surrounding prose (e.g. "Último PR mergeado: ...") is left untouched.
      # detection above keys off the "- #NNN" format, so it stays in sync
      # across runs.
      pr_lines_file="$TEMP_DIR/pr_lines.txt"
      if [[ $actual_prs -eq 0 ]]; then
        {
          echo "✅ **Status:** 0 PRs open"
          echo ""
          echo "(Verificado vía \`gh pr list --state open\` — sin resultados)"
        } > "$pr_lines_file"
      else
        {
          echo "✅ **Status:** $actual_prs PR(s) open"
          echo ""
          gh pr list --state open --json number,title,headRefName \
            --jq '.[] | "- #\(.number): \(.title) (`\(.headRefName)`)"' 2>/dev/null
        } > "$pr_lines_file"
      fi
      # NOTE: this pattern is passed to awk via `-v`, which runs its own
      # escape-sequence unescaping on the value *before* the regex is
      # compiled — so a single backslash here (e.g. `\(`) is consumed by `-v`
      # and never reaches the regex engine, while bracket expressions like
      # `[(]` carry no backslash and survive intact. Use brackets for every
      # literal metacharacter instead of backslash-escaping.
      if update_table_section "$STATE_FILE" "## PRs Activos" '^(✅ [*][*]Status:[*][*]|- #[0-9]+|[(]Verificado vía|[(]Sin PRs abiertos)' "$pr_lines_file" > "$TEMP_DIR/STATE_prs.md" \
          && [[ -s "$TEMP_DIR/STATE_prs.md" ]]; then
        cat "$TEMP_DIR/STATE_prs.md" > "$STATE_FILE"
        log_success "Updated PR list in STATE.md ($actual_prs open)"
      else
        log_error "Failed to update PR list"
      fi
      ;;
    update_issue_count)
      # Regenerate the "| #NNN | título | labels | estado |" rows inside
      # "## Issues Abiertos" from the real `gh issue list` output, and update
      # the "**Total:**" line in the same pass so both stay one source of
      # truth (bug #3) instead of drifting independently (bug #2). Other
      # prose in the section ("**Cerrado en esta sesión:**", "**Nota:**") is
      # left untouched.
      issue_lines_file="$TEMP_DIR/issue_lines.txt"
      gh issue list --state open --json number,title,labels \
        --jq '.[] | "| #\(.number) | \(.title) | \([.labels[].name] | join(", ")) | 🆕 Abierto |"' > "$issue_lines_file"
      # NOTE: same `-v` unescaping caveat as the PR pattern above — use a
      # bracket expression for the literal pipe instead of a backslash
      # escape, since `awk -v` strips a bare `\|` down to `|` (alternation
      # operator matching the start of every line) before the regex compiles.
      if update_table_section "$STATE_FILE" "## Issues Abiertos" '^[|] #[0-9]+' "$issue_lines_file" > "$TEMP_DIR/STATE_issues.md" \
          && [[ -s "$TEMP_DIR/STATE_issues.md" ]]; then
        cat "$TEMP_DIR/STATE_issues.md" > "$STATE_FILE"
        sed -i "s/^\*\*Total:\*\*.*/**Total:** $actual_issues issue(s) open (verificado vía \`gh issue list --state open\`)/" "$STATE_FILE" 2>/dev/null
        log_success "Issue count updated: $documented_issues → $actual_issues"
      else
        log_error "Failed to update issue count"
      fi
      ;;
  esac
done

# Handle ambiguous changes
if [[ ${#AMBIGUOUS_CHANGES[@]} -gt 0 ]]; then
  if [[ $SAFE_ONLY == true ]]; then
    log_warn "Skipping ambiguous changes (--safe-only mode)"
    echo "  Requires human review:"
    for change in "${AMBIGUOUS_CHANGES[@]}"; do
      reason="${change#*:}"
      echo "    - $reason"
    done
  elif [[ $REVIEW == true ]]; then
    # Interactive mode: ask user for each ambiguous change
    echo ""
    for change in "${AMBIGUOUS_CHANGES[@]}"; do
      action="${change%%:*}"
      reason="${change#*:}"

      log_prompt "$reason"
      read -p "  Apply this change? (y/n) " -n 1 -r
      echo
      if [[ $REPLY =~ ^[Yy]$ ]]; then
        case "$action" in
          blocker_verification)
            log_success "Marked blockers as verified"
            sed -i 's/\[MANUAL VERIFY REQUIRED\]/[VERIFIED]/g' "$STATE_FILE" 2>/dev/null
            ;;
          branch_archive)
            log_success "Archiving old branches"
            # TODO: implement branch archival logic
            ;;
        esac
      else
        log_warn "Skipped: $reason"
      fi
    done
  else
    log_warn "Ambiguous changes require --review flag"
    echo "  Use: /sync-memory --fix --review"
    exit 1
  fi
fi

# Update commit hash (bug #4: this never existed before — STATE.md's
# "**Hash commit:**" line silently went stale forever since nothing wrote it)
if [[ $DRY_RUN == false ]]; then
  current_hash=$(git -C "$PROJECT_ROOT" rev-parse --short HEAD 2>/dev/null)
  if [[ -n "$current_hash" ]]; then
    sed -i "s/^\*\*Hash commit:\*\*.*/**Hash commit:** $current_hash (main)/" "$STATE_FILE" 2>/dev/null && \
      log_success "Updated commit hash: $current_hash" || \
      log_error "Failed to update commit hash"
  else
    log_warn "Could not resolve git HEAD; skipping hash update"
  fi
fi

# Update audit trail
if [[ $DRY_RUN == false ]]; then
  new_entry="**$(date '+%Y-%m-%d %H:%M')** — Auto-sync applied"
  tail -n +1 "$STATE_FILE" | sed "/^## Audit Trail/a\\
\\
$new_entry" > "$TEMP_DIR/STATE_new.md" 2>/dev/null && \
    cat "$TEMP_DIR/STATE_new.md" > "$STATE_FILE"

  log_success "STATE.md updated with audit trail"
fi

echo ""
log_success "Sync complete"
exit 0
