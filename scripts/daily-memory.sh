#!/usr/bin/env bash
# daily-memory.sh - Generate comprehensive daily memory entries
#
# Replaces the previously too-brief daily memory.md entries with
# comprehensive, structured daily records. Integrates with the
# self-improving compound's HOT/WARM/COLD tiered memory system.
#
# Usage:
#   ./scripts/daily-memory.sh --root /path/to/workspace "Summary text"
#   cat daily-notes.md | ./scripts/daily-memory.sh --root /path/to/workspace
#   OPENCLAW_WORKSPACE=/path ./scripts/daily-memory.sh "Summary text"

set -euo pipefail

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------
ROOT=""
CONTENT=""
APPEND_MODE="false"

print_usage() {
    cat << 'USAGE'
Usage: daily-memory.sh [--root PATH] [--append] [SUMMARY]

Generate a comprehensive daily memory entry at memory/YYYY-MM-DD.md
in the workspace root. Outputs to both the file and stdout.

Options:
  --root PATH     Workspace root directory (default: $OPENCLAW_WORKSPACE or cwd)
  --append        Append a new timestamped section to an existing file
  --help          Show this help message

Content can be provided as:
  1. A positional argument after options:
     ./scripts/daily-memory.sh --root /path/to/workspace "Summarized daily content"

  2. Piped via stdin:
     cat daily-notes.md | ./scripts/daily-memory.sh --root /path/to/workspace

  3. Here-document:
     ./scripts/daily-memory.sh --root /path/to/workspace << 'EOF'
     Today I worked on...
     EOF

If no content is provided, the script prints this help and exits.

Environment:
  OPENCLAW_WORKSPACE    Default workspace root (overridden by --root)
USAGE
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --root)
            ROOT="$2"
            shift 2
            ;;
        --append)
            APPEND_MODE="true"
            shift
            ;;
        --help|-h)
            print_usage
            exit 0
            ;;
        --)
            shift
            CONTENT="$*"
            break
            ;;
        -*)
            echo "ERROR: Unknown option: $1" >&2
            print_usage >&2
            exit 1
            ;;
        *)
            CONTENT="$*"
            break
            ;;
    esac
done

# ---------------------------------------------------------------------------
# Resolve workspace root
# ---------------------------------------------------------------------------
if [ -z "$ROOT" ]; then
    ROOT="${OPENCLAW_WORKSPACE:-$(pwd)}"
fi

# Normalize to absolute path
ROOT="$(cd "$ROOT" 2>/dev/null && pwd || echo "$ROOT")"

if [ ! -d "$ROOT" ]; then
    echo "ERROR: Workspace root does not exist: $ROOT" >&2
    exit 1
fi

# ---------------------------------------------------------------------------
# Read content from stdin if not provided as argument
# ---------------------------------------------------------------------------
if [ -z "$CONTENT" ]; then
    # Check if stdin has data (not a terminal)
    if [ ! -t 0 ]; then
        CONTENT="$(cat)"
    fi
fi

if [ -z "$CONTENT" ]; then
    print_usage >&2
    exit 1
fi

# ---------------------------------------------------------------------------
# Prepare paths and timestamps
# ---------------------------------------------------------------------------
MEMORY_DIR="$ROOT/memory"
mkdir -p "$MEMORY_DIR"

TODAY="$(date +%Y-%m-%d)"
NOW_ISO="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
NOW_HUMAN="$(date '+%Y-%m-%d %H:%M:%S %Z')"
MEMORY_FILE="$MEMORY_DIR/$TODAY.md"

# ---------------------------------------------------------------------------
# Check for learnings.py integration
# ---------------------------------------------------------------------------
LEARNINGS_CLI=""
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -x "$SCRIPT_DIR/learnings.py" ]; then
    LEARNINGS_CLI="$SCRIPT_DIR/learnings.py"
elif command -v python3 &>/dev/null; then
    # Try to find learnings.py relative to workspace
    for candidate in \
        "$ROOT/scripts/learnings.py" \
        "$ROOT/../scripts/learnings.py" \
        "$HOME/self-improving/scripts/learnings.py"; do
        if [ -x "$candidate" ]; then
            LEARNINGS_CLI="$candidate"
            break
        fi
    done
fi

# ---------------------------------------------------------------------------
# Build the daily entry
# ---------------------------------------------------------------------------

build_entry() {
    local content="$1"
    local today="$2"
    local now_iso="$3"
    local now_human="$4"
    local append_mode="$5"
    local learnings_cli="$6"
    local root="$7"

    # If appending, add a separator and timestamp header
    if [ "$append_mode" = "true" ] && [ -f "$MEMORY_FILE" ]; then
        cat << SECTION_SEPARATOR

---

## Appended Session: $now_human

SECTION_SEPARATOR
    fi

    # Generate the structured daily entry
    cat << ENTRY_TEMPLATE
# Daily Memory: $today

> Generated: $now_iso | Workspace: \`$root\`

## Session Overview
- **Active Duration**: [fill in time range]
- **Primary Focus**: $content
- **Mood/Tone**: [productive / debugging / exploratory / learning]

## Tasks Completed
- [ ] [Task 1 - brief description]
- [ ] [Task 2 - brief description]
- [ ] [Task 3 - brief description]

## Key Decisions Made
- **Decision**: [what was decided]
  - **Rationale**: [why this choice]
  - **Alternatives Considered**: [what else was on the table]

## Errors Encountered & Resolved
- **Error**: [description of the failure]
  - **Root Cause**: [why it happened]
  - **Resolution**: [how it was fixed]
  - **Should Be Logged to learnings?**: [YES / NO — with pattern-key suggestion]

## New Learnings
- **Learning**: [what was learned]
  - **Context**: [when and where this applies]
  - **Pattern-Key Suggestion**: [e.g., \`docker-build-cache\`, \`api-pagination-defaults\`]

## Corrections Applied
- **Correction**: [what was corrected]
  - **Previous Understanding**: [the wrong belief or assumption]
  - **Correct Understanding**: [the right answer or approach]

## Skills Discovered / Refined
- **Skill**: [skill name or description]
  - **Source**: [external docs / debug session / user taught / trial-and-error]
  - **Reusability**: [project-specific / domain-general / universal]

## Pending / Follow-up
- [ ] [Item 1 — context and priority]
- [ ] [Item 2 — context and priority]
- [ ] [Item 3 — context and priority]

## Self-Improvement Audit
- [ ] Did I capture all non-obvious failures to \`learning/self-improving/\`?
- [ ] Did any Pattern-Key reach Recurrence-Count >= 3?
- [ ] Did I promote any learnings to project or domain memory?
- [ ] Did I identify any new reusable skills?

## Raw Input
\`\`\`
$content
\`\`\`
ENTRY_TEMPLATE
}

ENTRY="$(build_entry "$CONTENT" "$TODAY" "$NOW_ISO" "$NOW_HUMAN" "$APPEND_MODE" "$LEARNINGS_CLI" "$ROOT")"

# ---------------------------------------------------------------------------
# Write to file
# ---------------------------------------------------------------------------
if [ "$APPEND_MODE" = "true" ] && [ -f "$MEMORY_FILE" ]; then
    echo "$ENTRY" >> "$MEMORY_FILE"
    echo "[daily-memory] Appended session to: $MEMORY_FILE" >&2
else
    echo "$ENTRY" > "$MEMORY_FILE"
    echo "[daily-memory] Created: $MEMORY_FILE" >&2
fi

# ---------------------------------------------------------------------------
# Output to stdout
# ---------------------------------------------------------------------------
echo "$ENTRY"

# ---------------------------------------------------------------------------
# Optional: suggest learnings.py integration
# ---------------------------------------------------------------------------
if [ -n "$LEARNINGS_CLI" ]; then
    cat >&2 << HINT

[daily-memory] Tip: Review the entry above and log durable lessons with:
  python3 $LEARNINGS_CLI --root "$ROOT" log-learning "Your lesson summary"
  python3 $LEARNINGS_CLI --root "$ROOT" log-correction "What was corrected"

HINT
fi