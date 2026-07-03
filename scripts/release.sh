#!/usr/bin/env bash
set -euo pipefail

# Release script: tags and creates a GitHub Release from current dev HEAD.
# Usage: ./scripts/release.sh <version> [--dry-run]
#   version: semver tag, e.g. v1.0.0-alpha
#   --dry-run: print what would be done without making changes

if [ $# -lt 1 ]; then
    echo "Usage: $0 <version> [--dry-run]"
    exit 1
fi

VERSION="$1"
DRY_RUN="${2:-}"
BRANCH="$(git rev-parse --abbrev-ref HEAD)"

# Pre-flight checks
if [ "$BRANCH" != "dev" ]; then
    echo "ERROR: must be on dev branch (currently on $BRANCH)"
    exit 1
fi

if ! git diff --quiet --exit-code; then
    echo "ERROR: working tree has uncommitted changes — commit or stash first"
    exit 1
fi

git fetch origin dev 2>/dev/null || true
BEHIND=$(git rev-list --count "HEAD..origin/dev" 2>/dev/null || echo 0)
if [ "$BEHIND" -gt 0 ]; then
    echo "ERROR: local dev is $BEHIND commits behind origin/dev — pull first"
    exit 1
fi

# Check version format
if ! echo "$VERSION" | grep -qE '^v[0-9]+\.[0-9]+\.[0-9]+'; then
    echo "ERROR: version must be semver (e.g. v1.0.0-alpha)"
    exit 1
fi

echo "◆ Releasing $VERSION from dev"
echo "  Branch: $BRANCH"
echo "  Commit: $(git rev-parse --short HEAD)"
echo ""

if [ "$DRY_RUN" = "--dry-run" ]; then
    echo "◆ DRY RUN — no changes made"
    echo "  Would: git tag $VERSION"
    echo "  Would: git push origin $VERSION"
    echo "  Would: gh release create $VERSION --generate-notes --title '$VERSION' --target dev"
    exit 0
fi

echo "◆ Creating tag $VERSION..."
git tag "$VERSION"

echo "◆ Pushing tag..."
git push origin "$VERSION"

echo "◆ Creating GitHub Release..."
gh release create "$VERSION" \
    --generate-notes \
    --title "$VERSION" \
    --target dev \
    --draft

echo ""
echo "✅ Release $VERSION created (draft)"
echo "   View: https://github.com/germanf/agent-os/releases/tag/$VERSION"
echo ""
echo "   Next step: publish the draft release on GitHub, then PR dev→main for production."
