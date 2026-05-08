#!/usr/bin/env bash
# extract-skill.sh - Extract a reusable skill from learning records
# Adapted from tristanmanchester + pskoett best practices

set -euo pipefail

SKILL_NAME="${1:-}"
WORKSPACE_ROOT="${2:-$HOME/.openclaw/workspace}"
LEARNINGS_DIR="$HOME/self-improving"

if [ -z "$SKILL_NAME" ]; then
    echo "Usage: extract-skill.sh <skill-name> [workspace-root]"
    echo "Example: extract-skill.sh docker-build-fixes"
    exit 1
fi

SKILL_DIR="$WORKSPACE_ROOT/skills/$SKILL_NAME"
mkdir -p "$SKILL_DIR"

cat > "$SKILL_DIR/SKILL.md" << EOF
---
name: $SKILL_NAME
description: "Extracted from self-improving learning records. Use when: [fill from learning]."
metadata:
  source: "self-improving/extract"
  extracted_at: "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
---

# $SKILL_NAME

## When to Use

[Auto-filled from learning record]

## Core Rules

[Auto-filled from learning record]

## Quick Reference

| Situation | Action |
|-----------|--------|

## References

- Source learning: [link to original record]
EOF

echo "[extract] Skill scaffold created: $SKILL_DIR/SKILL.md"
echo "[extract] Next steps:"
echo "  1. Edit $SKILL_DIR/SKILL.md to fill rules and references"
echo "  2. Add scripts/ or references/ if needed"
echo "  3. Test before installing: clawhub install $SKILL_NAME --dir /tmp/test"
