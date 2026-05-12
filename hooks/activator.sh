#!/usr/bin/env bash
set -euo pipefail

WORKSPACE_ROOT="${OPENCLAW_WORKSPACE:-$(pwd)}"
MEMORY_FILE="$WORKSPACE_ROOT/learning/self-improving/memory.md"

if [ ! -f "$MEMORY_FILE" ]; then
    exit 0
fi

CONTEXT="${1:-}"
MATCHES=$(grep -h "\[Pattern-Key:" "$MEMORY_FILE" 2>/dev/null | sed 's/.*Pattern-Key: *//; s/\].*//' | sort | uniq -c | sort -rn | head -5)

if [ -n "$MATCHES" ]; then
    echo ""
    echo "[activator] Relevant patterns for current context:"
    echo "$MATCHES" | while read -r COUNT KEY; do
        printf "  - %s (%s occurrences)\n" "$KEY" "$COUNT"
    done
    echo ""
fi
