#!/bin/bash
# Cleanup script for orphaned worktrees and their agent branches
# Usage: ./cleanup-worktrees.sh [--dry-run]
# Purpose: Remove abandoned worktrees and the agent branches left behind on
# origin once the local worktree is already gone (see incident: branch
# worktree-agent-afd3bab028e74bb18 survived for days because nothing ever
# deleted the remote branch — only the local checkout).

set -e

DRY_RUN=false
if [ "${1:-}" == "--dry-run" ]; then
    DRY_RUN=true
    echo "🔍 DRY RUN: Showing what would be deleted (no changes)"
    echo ""
fi

# ── Step 1: remove orphaned local worktrees ────────────────────────────────

BEFORE=$(git worktree list | wc -l)
WORKTREES=$(git worktree list | grep -E "agent-|worktree-agent-" | awk '{print $1}' || true)

if [ -z "$WORKTREES" ]; then
    echo "✅ No orphaned worktrees found"
else
    echo "🗑️  Found orphaned worktrees:"
    git worktree list | grep -E "agent-|worktree-agent-"
    echo ""

    REMOVED=0
    while IFS= read -r worktree; do
        [ -z "$worktree" ] && continue
        if [ "$DRY_RUN" == true ]; then
            echo "Would remove worktree: $worktree"
            continue
        fi
        echo "Removing: $worktree"
        # Use -f -f to force remove even if locked
        if git worktree remove -f -f "$worktree" 2>/dev/null; then
            REMOVED=$((REMOVED + 1))
        else
            echo "  ⚠️  Failed to remove (may already be removed)"
        fi
    done <<< "$WORKTREES"

    AFTER=$(git worktree list | wc -l)
    echo ""
    echo "✅ Worktree cleanup complete:"
    echo "   Before: $BEFORE worktrees"
    echo "   After: $AFTER worktrees"
    echo "   Removed: ${REMOVED:-0}"
    SPACE_FREED=$(( ${REMOVED:-0} * 250 ))
    echo "   Space freed (est.): ~${SPACE_FREED}MB"
fi

# ── Step 2: delete stale agent branches on origin ──────────────────────────
# Worktree removal above only deletes the local checkout dir. By the time this
# script runs, the local worktree for a finished agent is often already gone
# (torn down by ExitWorktree), so step 1 never even sees its branch. This step
# catches those directly on origin instead of relying on a live local worktree.

echo ""
echo "🔎 Scanning origin for stale agent branches..."
git fetch origin --prune --quiet

CANDIDATES=$(git for-each-ref --format='%(refname:short)' refs/remotes/origin |
    grep -E "^origin/(agent-|worktree-agent-)" | sed 's#^origin/##' || true)

if [ -z "$CANDIDATES" ]; then
    echo "✅ No agent branches found on origin"
    exit 0
fi

DELETED=0
for branch in $CANDIDATES; do
    # Still backing a live local worktree — leave it alone.
    if git worktree list | grep -q "\[$branch\]"; then
        continue
    fi

    # Open PR — in-progress work, not orphaned.
    if command -v gh >/dev/null 2>&1; then
        OPEN_PR=$(gh pr list --head "$branch" --state open --json number --jq 'length' 2>/dev/null) && GH_STATUS=0 || GH_STATUS=$?
        if [ "$GH_STATUS" != "0" ]; then
            echo "  ⚠️  $branch — could not verify open-PR status (gh failed), skipping out of caution"
            continue
        fi
        if [ "$OPEN_PR" != "0" ]; then
            echo "  ⏭️  $branch — has an open PR, leaving it"
            continue
        fi
    fi

    # Safe to auto-delete only if every commit is already reachable from main
    # (literal ancestor) or patch-equivalent to something already in main
    # (e.g. squash-merged). Anything else has unique unmerged work and needs a
    # human/agent to verify it's actually superseded before deleting — see the
    # worktree-agent-afd3bab028e74bb18 review for what that check looks like.
    if git merge-base --is-ancestor "origin/$branch" origin/main 2>/dev/null; then
        SAFE=true
    elif [ -z "$(git cherry origin/main "origin/$branch" 2>/dev/null | grep '^+')" ]; then
        SAFE=true
    else
        SAFE=false
    fi

    if [ "$SAFE" == true ]; then
        if [ "$DRY_RUN" == true ]; then
            echo "  Would delete merged stale branch: $branch"
        else
            echo "  🗑️  Deleting merged stale branch: $branch"
            git push origin --delete "$branch" 2>/dev/null || echo "    ⚠️  Failed to delete origin/$branch"
        fi
        DELETED=$((DELETED + 1))
    else
        echo "  ⚠️  $branch has unmerged unique commits — no open PR, needs manual review (not auto-deleting)"
    fi
done

echo ""
echo "✅ Branch scan complete: ${DELETED} stale branch(es) $( [ "$DRY_RUN" == true ] && echo "would be " )deleted"
