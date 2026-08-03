#!/usr/bin/env bash
# =============================================================================
# scripts/check_f401.sh — F401 Unused Import Gate
#
# Purpose: Check that no NEW F401 (unused import) violations are introduced.
# Uses an allowlist of known pre-existing violations so the team can fix them
# incrementally while blocking regressions.
#
# Usage:
#   ./scripts/check_f401.sh                     # check mode (CI / pre-commit)
#   ./scripts/check_f401.sh --update-allowlist   # update allowlist from current state
#   ./scripts/check_f401.sh --help               # show this help
#
# Exit codes:
#   0 — no new violations (or allowlist updated)
#   1 — new violations detected (report only)
#   2 — unexpected error (missing toolchain, etc.)
#
# Environment variables:
#   F401_TARGETS   — ruff targets (default: "src/ spine_api/ tests/")
#   F401_ALLOWLIST — path to allowlist (default: ./scripts/.f401_allowlist)
#
# CI integration:
#   Add to .github/workflows/ci.yml:
#     - name: F401 unused import gate
#       run: bash scripts/check_f401.sh
#
# To fix a violation, remove the import. Then regenerate the allowlist:
#   ./scripts/check_f401.sh --update-allowlist
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# ── Config ──────────────────────────────────────────────────────────────────
F401_TARGETS="${F401_TARGETS:-src/ spine_api/ tests/}"
F401_ALLOWLIST="${F401_ALLOWLIST:-$SCRIPT_DIR/.f401_allowlist}"

# ── Colors (for local DX, stripped in CI) ───────────────────────────────────
if [ -t 1 ] && [ -n "$TERM" ] && [ "$TERM" != "dumb" ]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    CYAN='\033[0;36m'
    BOLD='\033[1m'
    NC='\033[0m'
else
    RED='' GREEN='' YELLOW='' CYAN='' BOLD='' NC=''
fi

# ── Help ────────────────────────────────────────────────────────────────────
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
    sed -n '3,/^# =/p' "${BASH_SOURCE[0]}" | sed 's/^# //; s/^#$//' | grep -v '^ ='
    exit 0
fi

# ── Prerequisites ───────────────────────────────────────────────────────────
if ! command -v uv >/dev/null 2>&1; then
    echo "check_f401: ERROR — 'uv' not found. Install uv (https://docs.astral.sh/uv/) and retry." >&2
    exit 2
fi

if ! uv run ruff --version >/dev/null 2>&1; then
    echo "check_f401: ERROR — 'ruff' not available via uv. Run 'uv sync' first." >&2
    exit 2
fi

# ── Generate current F401 report ────────────────────────────────────────────
_generate_report() {
    uv run ruff check --select F401 --output-format=concise $F401_TARGETS 2>/dev/null \
      | grep -v '^Found ' \
      | grep -v '^All checks passed' \
      || true
}

# ── Count violations in a report ────────────────────────────────────────────
_count_violations() {
    local report="$1"
    local n
    n=$(echo "$report" | grep -cE '^[a-zA-Z]' 2>/dev/null || true)
    echo "${n:-0}"
}

# ── Normalize a report (strip trailing whitespace) ─────────────────────
_normalize_report() {
    local report="$1"
    echo "$report" | sed 's/[[:space:]]*$//'
}

# ── Update allowlist ────────────────────────────────────────────────────────
if [ "${1:-}" = "--update-allowlist" ]; then
    echo "check_f401: Generating F401 allowlist from current state..." >&2

    report="$(_generate_report)"
    count="$(_count_violations "$report")"

    cat > "$F401_ALLOWLIST" <<< "$report"

    if [ "$count" -gt 0 ]; then
        echo -e "${GREEN}check_f401:${NC} Allowlist updated with ${BOLD}${count}${NC} known F401 violation(s)." >&2
    else
        echo -e "${GREEN}check_f401:${NC} Allowlist updated — zero violations. Clean slate!" >&2
    fi
    exit 0
fi

# ── Ensure allowlist exists ─────────────────────────────────────────────────
if [ ! -f "$F401_ALLOWLIST" ]; then
    echo -e "${YELLOW}check_f401:${NC} No allowlist found at ${F401_ALLOWLIST}." >&2
    echo -e "${YELLOW}check_f401:${NC} Run '${BOLD}$0 --update-allowlist${NC}' to generate one from current state." >&2
    echo -e "${YELLOW}check_f401:${NC} Until then, all F401 violations are considered NEW." >&2
    echo "" >&2
    F401_ALLOWLIST="/dev/null"
fi

# ── Compare ─────────────────────────────────────────────────────────────────
echo "check_f401: Scanning for F401 (unused import) violations..." >&2

current="$(_generate_report)"
current_count="$(_count_violations "$current")"
allowlist_count="$(_count_violations "$(cat "$F401_ALLOWLIST")")"

# Find new violations — lines in current report that aren't in the allowlist
# We use a simple line-by-line comparison. Ruff output is deterministic for
# the same code, so exact matching is reliable.
new_violations=""
new_count=0

while IFS= read -r line; do
    if [ -n "$line" ]; then
        if ! grep -Fxq "$line" "$F401_ALLOWLIST" 2>/dev/null; then
            new_violations="${new_violations}${line}"$'\n'
            new_count=$((new_count + 1))
        fi
    fi
done <<< "$current"

# Find fixed violations (in allowlist but no longer in current output)
fixed_count=0
while IFS= read -r line; do
    if [ -n "$line" ]; then
        if ! grep -Fxq "$line" <(echo "$current") 2>/dev/null; then
            fixed_count=$((fixed_count + 1))
        fi
    fi
done < "$F401_ALLOWLIST"

# ── Report ──────────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}F401 Unused Import Gate Summary${NC}"
echo "  Current violations:  ${current_count}"
echo "  Allowlisted:         ${allowlist_count}"
echo "  New violations:      ${new_count}"
echo "  Fixed violations:    ${fixed_count}"
echo ""

if [ "$new_count" -gt 0 ]; then
    echo -e "${RED}${BOLD}❌  ${new_count} NEW unused import(s) detected — must be fixed before merge:${NC}"
    echo ""
    echo "$new_violations" | while IFS= read -r violation; do
        if [ -n "$violation" ]; then
            # Parse file:line:col: code message
            file="${violation%%:*}"
            rest="${violation#*:}"
            line="${rest%%:*}"
            rest="${rest#*:}"
            col="${rest%%:*}"
            message="${rest#*:}"
            message="${message# F401 }"
            echo -e "  ${RED}✗${NC} ${BOLD}$file${NC}:${line}:${col} — ${message}"
        fi
    done
    echo ""
    echo -e "${YELLOW}Tip:${NC} Remove the unused import, then run:"
    echo -e "  ${CYAN}$0 --update-allowlist${NC}"
    echo ""
    exit 1
else
    echo -e "${GREEN}${BOLD}✅  No new F401 violations.${NC}"
    if [ "$fixed_count" -gt 0 ]; then
        echo -e "${GREEN}  🎉  ${fixed_count} pre-existing violation(s) have been fixed!${NC}"
        echo -e "      Run '${CYAN}$0 --update-allowlist${NC}' to shrink the allowlist."
    fi
    exit 0
fi
