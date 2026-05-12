#!/usr/bin/env bash
set -euo pipefail

WORKSPACE_ROOT="${OPENCLAW_WORKSPACE:-$(pwd)}"
CORRECTIONS_FILE="$WORKSPACE_ROOT/learning/self-improving/corrections.md"

ERROR_TYPE="${1:-general}"
ERROR_DETAIL="${2:-}"

if [ -z "$ERROR_DETAIL" ]; then
    exit 0
fi

if [ -f "$CORRECTIONS_FILE" ]; then
    TODAY=$(date +%Y-%m-%d)
    ID=$(python3 -c "
import sys
from datetime import datetime
base = datetime.now().strftime('ERR-%Y%m%d')
seq = 1
with open('$CORRECTIONS_FILE', 'r') as f:
    for line in f:
        if line.startswith(f'| {base}'):
            seq += 1
print(f'{base}-{seq:03d}')
")

    printf "| %s | %s | %s | %s | | ⏳ pending |\n" "$ID" "$TODAY" "$ERROR_TYPE" "$ERROR_DETAIL" >> "$CORRECTIONS_FILE"
    echo "[error-detector] Logged error: $ID"
fi
