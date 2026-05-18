#!/usr/bin/env bash
# Wire scripts/hooks/ as the active git hooks directory for this repo.
#
# Run once per clone or worktree:
#   bash scripts/install-git-hooks.sh
#
# This sets core.hooksPath in the local .git/config (not committed).
# Once set, git ignores .git/hooks/ entirely and uses scripts/hooks/ instead.
# The existing .git/hooks/commit-msg (if present) becomes inert — it is
# superseded by the tracked scripts/hooks/commit-msg with identical behavior.

set -e

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

git config core.hooksPath scripts/hooks
chmod +x scripts/hooks/pre-commit scripts/hooks/commit-msg

echo ""
echo "Git hooks installed."
echo "  core.hooksPath = $(git config --get core.hooksPath)"
echo ""
echo "Active hooks:"
ls -1 scripts/hooks/ | grep -v '\.sample' | sed 's/^/  /'
echo ""
echo "Verify trailer guard (should exit 1):"
echo "  printf 'test\n\nCo-Authored-By: Claude Sonnet 4.6 <x>\n' | scripts/hooks/commit-msg /dev/stdin"
echo ""
echo "Verify motto guard (should exit 0 with intact motto_v2.md):"
echo "  scripts/hooks/pre-commit"
echo ""
