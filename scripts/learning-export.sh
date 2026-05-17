#!/usr/bin/env bash
set -euo pipefail
ROOT="${OPENCLAW_WORKSPACE:-/home/rockway/.openclaw/workspace}"
SKILL_DIR="${SELF_IMPROVING_SKILL_DIR:-$ROOT/skills/self-improving-compound}"
OUT="$ROOT/learning/memory-export.md"
python3 "$SKILL_DIR/scripts/learnings.py" --root "$ROOT" export --output "$OUT"
python3 "$SKILL_DIR/scripts/learnings.py" --root "$ROOT" status --format json > "$ROOT/learning/status.json"
echo "[learning-export] wrote $OUT"
