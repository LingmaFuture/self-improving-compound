#!/usr/bin/env bash
set -euo pipefail
ROOT="${OPENCLAW_WORKSPACE:-/home/rockway/.openclaw/workspace}"
SKILL_DIR="${SELF_IMPROVING_SKILL_DIR:-$ROOT/skills/self-improving-compound}"
LOG="$ROOT/learning/system-failure-audit.log"
mkdir -p "$ROOT/learning"
{
  echo "# system failure audit $(date -Is)"
  if command -v openclaw >/dev/null 2>&1; then
    echo "## openclaw status"
    openclaw status 2>&1 || true
    echo "## gateway status"
    openclaw gateway status 2>&1 || true
    if openclaw help 2>/dev/null | grep -q '\bdoctor\b'; then
      echo "## openclaw doctor"
      openclaw doctor 2>&1 || true
    fi
  else
    echo "openclaw CLI not found"
  fi
} > "$LOG.tmp"
mv "$LOG.tmp" "$LOG"
if grep -Eiq '(^|[^a-z])(error|failed|failure|unhealthy|critical|panic|exception|traceback)([^a-z]|$)' "$LOG"; then
  SUMMARY=$(grep -Ei 'error|failed|failure|unhealthy|critical|panic|exception|traceback' "$LOG" | head -5 | tr '\n' '; ' | cut -c1-500)
  python3 "$SKILL_DIR/scripts/learnings.py" --root "$ROOT" search "$SUMMARY" --limit 3 | grep -q 'No results' && \
  python3 "$SKILL_DIR/scripts/learnings.py" --root "$ROOT" log-error \
    --summary "OpenClaw system audit detected failure signal" \
    --details "${SUMMARY}. Full audit log: $LOG" \
    --pattern "system:openclaw-audit-failure" \
    --area "domain:openclaw" \
    --force || true
fi
echo "[system-failure-audit] wrote $LOG"
