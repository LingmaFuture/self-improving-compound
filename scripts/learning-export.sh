#!/usr/bin/env bash
set -euo pipefail
ROOT="${OPENCLAW_WORKSPACE:-$PWD}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="${SELF_IMPROVING_SKILL_DIR:-$(dirname "$SCRIPT_DIR")}"
LEARNINGS_CLI="${SELF_IMPROVING_LEARNINGS_CLI:-$SKILL_DIR/scripts/learnings.py}"
OUT="$ROOT/learning/memory-export.md"
mkdir -p "$ROOT/learning"
python3 "$LEARNINGS_CLI" --root "$ROOT" export --output "$OUT"
python3 "$LEARNINGS_CLI" --root "$ROOT" status --format json > "$ROOT/learning/status.json"
echo "[learning-export] wrote $OUT"
