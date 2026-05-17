# Self-Improving Compound

An agent memory and self-improvement system built as a composite of the best practices from major self-improving agent frameworks. Replaces naive file-based agent memory with a structured SQLite learning engine, automated cron-based audit pipeline, and continuous skill/agent-instruction promotion.

- **OpenClaw stock** (v1.2.16) — the built-in HOT/WARM/COLD lifecycle vocabulary
- **OpenHuman** — SQLite memory-tree storage, entity index, scoring, and lifecycle metadata
- **tristanmanchester/actual-self-improvement** — Python toolchains, structured logging, JSON evals
- **pskoett/self-improving-agent** — quantified promotion thresholds, OpenClaw hooks, pattern-key recurrence rules
- **GenericAgent** (MIT) — memory hygiene axioms: action-verified memory, volatile-state avoidance, pointer/index hygiene

## Architecture

## System positioning

This is not just a skill — it is a **memory system**. It installs alongside your agent runtime and takes over execution learning, replacing flat markdown files with a structured pipeline:

- **SQLite memory-tree** () — source of truth for all learnings, with scoring, lifecycle, entity indexing, and deduplication.
- **Cron audit architecture** — isolated background jobs that scan session history, catch missed lessons, maintain lifecycle, and export for review.
- **Capture gate routing** — lessons flow to the right destination by type: facts to , mistakes to , rules to , behavior to .
- **7+3 co-evolution** — all seven markdown files and three directories improve together; fixing one layer while leaving another stale is half-done work.

This is a **hybrid design**: actual-self-improvement serves as the execution core, while self-improving-compound provides the memory architecture, and the local agent lineage contributes promotion rules and hook guidance.

### Skill root (bundled resources)

```
.
├── SKILL.md                          # Portable AgentSkill frontmatter + rules
├── scripts/
│   ├── learnings.py                  # SQLite-first CLI: init, status, search, log, promote, edit, maintain, export
│   ├── extract-skill.sh              # Extract reusable skill from learnings
│   └── daily-memory.sh               # Generate daily notes under learning/daily/
├── hooks/
│   ├── activator.sh                  # Reminder at session start
│   └── error-detector.sh             # Suggest logging after failures
├── evals/
│   ├── trigger-validation.json       # Quality gate: did we trigger correctly?
│   └── output-evals.json             # Quality gate: is the entry well-formed?
├── references/
│   ├── entry-formats.md              # Full field schemas and manual templates
│   ├── promotion-and-extraction.md   # Promotion rules and skill extraction criteria
│   ├── platform-setup.md             # Claude Code, Codex, Copilot, and OpenClaw setup
│   ├── heartbeat-guidance.md         # Heartbeat integration for periodic checks
│   └── hermes-integration.md         # Hermes Agent architecture concepts absorbed
└── CHANGELOG.md
```

### Workspace root (data lives here)

```
<workspace-root>/
└── learning/
    ├── memory_tree/chunks.db  # SQLite source of truth
    ├── index.md               # SQLite-generated snapshot (entries, lifecycle, pattern keys)
    ├── projects/              # Legacy/import workspace namespace
    ├── domains/               # Legacy/import workspace namespace
    └── archive/               # Legacy/export workspace namespace
```

## Install

### As a portable AgentSkill

1. Copy or symlink this directory into your skills location:
   ```bash
   cp -r self-improving-compound ~/.openclaw/skills/self-improving-compound
   ```

2. Ensure `scripts/learnings.py` is executable:
   ```bash
   chmod +x scripts/learnings.py scripts/extract-skill.sh hooks/*.sh
   ```

### Requirements

- Python 3.9+
- bash (for hook scripts)
- No network access required

## Hardening automation

This package includes `scripts/learning-audit.py`, `scripts/log-system-failures.sh`, and `scripts/learning-export.sh` for capture-gate audits, runtime failure logging, and daily SQLite exports.

## Quick Start

```bash
# 1. Initialize structure in a workspace
python3 scripts/learnings.py --root /path/to/workspace init

# 2. Log a correction
python3 scripts/learnings.py --root /path/to/workspace log-correction \
  --summary "Used wrong format for Telegram" \
  --correct "Use lists, not tables" \
  --pattern chat:telegram-format

# 3. Log a learning
python3 scripts/learnings.py --root /path/to/workspace log-learning \
  --summary "Always search before logging" \
  --details "Avoid duplicate long-term memory entries" \
  --pattern memory:dedup-rule

# 4. Search
python3 scripts/learnings.py --root /path/to/workspace search "telegram"
python3 scripts/learnings.py --root /path/to/workspace search "telegram" --format json
python3 scripts/learnings.py --root /path/to/workspace search "telegram" --touch

# 5. Check status
python3 scripts/learnings.py --root /path/to/workspace status
python3 scripts/learnings.py --root /path/to/workspace status --format json

# 6. Review and maintain memory lifecycle (dry-run by default)
python3 scripts/learnings.py --root /path/to/workspace maintain
python3 scripts/learnings.py --root /path/to/workspace maintain --format json
python3 scripts/learnings.py --root /path/to/workspace maintain --apply

# 7. Promote a proven learning to project memory
python3 scripts/learnings.py --root /path/to/workspace promote LRN-20260512-001 --to CLAUDE.md

# 8. Edit entry status/metadata
python3 scripts/learnings.py --root /path/to/workspace edit COR-20260512-001 --status resolved

# 9. Extract a skill from accumulated learnings
bash scripts/extract-skill.sh my-skill-name /path/to/workspace

# 10. Generate comprehensive daily memory under learning/daily/
bash scripts/daily-memory.sh --root /path/to/workspace "Summary text"
```

`--root` can be placed either before the subcommand (global) or after it (command-local). Both forms are supported.

## Path model

There are **two different roots**:

1. **Skill root** — where this repository lives (scripts, references, hooks).
2. **Workspace root** — where `learning/` is created and written.

Never write learnings into the skill directory. Always target the workspace root.

Durable entries are stored in `learning/memory_tree/chunks.db`. A lightweight `index.md` is auto-generated as a human-readable snapshot. Use the `learnings.py` CLI for queries and management.

The workspace root is resolved in this order:
1. `--root /path/to/workspace` (explicit, either before or after the subcommand)
2. `OPENCLAW_WORKSPACE` environment variable
3. Current working directory

Dates and IDs use the system local timezone by default. Set `SOURCE_DATE_EPOCH` for reproducible builds.

## Key Features Absorbed

| Source | Feature | How It's Integrated |
|--------|---------|---------------------|
| **stock** | HOT/WARM/COLD lifecycle | Mapped to SQLite lifecycle statuses (`admitted`, `buffered`, `sealed`) |
| **OpenHuman** | Memory-tree storage | `learning/memory_tree/chunks.db` with chunks, scores, entity index, hotness, jobs, and ingested-source dedupe |
| **stock** | Automatic promotion (30d/90d) | Enforced by `maintain` with `--dry-run` and `--apply`; updates lifecycle status without deleting content |
| **stock** | Namespace isolation (projects/domains/archive) | Native directory structure |
| **tristanmanchester** | `learnings.py` CLI | Adapted to hybrid directory layout with `--root` support |
| **tristanmanchester** | `extract_skill.py` | Simplified to bash + scaffold |
| **tristanmanchester** | Evals framework | JSON evals: `trigger-validation.json` + `output-evals.json` |
| **tristanmanchester** | Pattern-Key stable identifiers | Built into logging commands and auto-index |
| **pskoett** | `TYPE-YYYYMMDD-XXX` ID format | Preserved as human entry IDs; internal chunks keep content-addressed IDs |
| **pskoett** | Quantified promotion threshold | `Recurrence-Count >= 3` flags a candidate; task-span review remains manual |
| **pskoett** | Hooks (activator + error-detector) | Simplified bash versions, workspace-root aware |
| **GenericAgent** | Memory hygiene (action-verified, no volatile state, pointer hygiene) | Rules in `references/promotion-and-extraction.md`, validation in `scripts/learnings.py` |
| **ivangdavila** | Human-like memory lifecycle | `maintain` subcommand with lifecycle promotion/demotion/archive markers |
| **ivangdavila** | HOT/WARM/COLD limits & namespace specificity | Tier enforcement is implemented; specificity conflict resolution is guidance |
| **ivangdavila** | Compaction by summarization/merge | Export/manual promotion support; automatic summarization is intentionally not implemented |
| **ivangdavila** | Heartbeat maintenance guidance | `references/heartbeat-guidance.md` with periodic `maintain --dry-run` |
| **ivangdavila** | Transparent source/pointer hygiene | Metadata fields + citation-ready entries |

## Memory Lifecycle

This skill integrates a human-like memory lifecycle inspired by `ivangdavila/self-improving`:

| Tier | Location | Trigger | Behavior |
|------|----------|---------|----------|
| **HOT** | SQLite `admitted` chunks | Active use | Shown by `status`, `search`, and hooks; entries include `First-Seen`, `Last-Seen`, `Recurrence-Count`, `Status`, and `Area` metadata |
| **WARM** | SQLite `buffered` chunks | Demoted from HOT after 30 days unused | Retained for context-specific search; preserves full history |
| **COLD** | SQLite `sealed` chunks | Archived/promoted/resolved or stale WARM | Retained for explicit query/export; never deleted without explicit action |

### Automatic lifecycle rules

The `maintain` command enforces these rules safely:

| Condition | Threshold | Action |
|-----------|-----------|--------|
| HOT -> WARM | 30 days unused | Mark entry `buffered` |
| WARM -> COLD | 90 days unused | Mark entry `sealed` |
| Frequent reuse | `Recurrence-Count >= 3` | Flag for project-memory promotion |
| Compaction/export | Human review needed | Export and manually summarize/promote without deleting the SQLite record |

### Conflict resolution

When patterns contradict, the following precedence applies:

1. **More specific wins**: `project` > `domain` > `global`
2. **More recent wins** at the same specificity level
3. **Ambiguous conflicts** require asking the user instead of guessing

### Maintenance safety

- `maintain` defaults to `--dry-run`; use `--apply` to execute moves.
- Content is never deleted; lifecycle status is updated, and markdown exports/promotions are append-only.
- `maintain` uses explicit `Recurrence-Count` metadata; plain search is read-only, while `search --touch` records actual reuse.
- If metadata is insufficient, `maintain` reports recommendations rather than making destructive guesses.
- The heartbeat guidance (see `references/heartbeat-guidance.md`) suggests running `maintain --dry-run` periodically.

## Promotion Rules

| Tier | Condition | Action |
|------|-----------|--------|
| HOT -> WARM | 30 days unused | Mark `buffered` |
| WARM -> COLD | 90 days unused | Mark `sealed` |
| Frequent reuse | 3 recorded uses within 7 days | Promote as short prevention rule |
| To AGENTS/SOUL/TOOLS | Proven + broadly applicable | Promote as short prevention rule |
| To skill | Proven + broadly applicable | Extract as skill |

## Migration from prior versions

### From `actual-self-improvement`

- Move existing `learnings/LEARNINGS.md`, `learnings/ERRORS.md`, `learnings/FEATURE_REQUESTS.md` into `learning/` if desired, or keep them alongside.
- The CLI now uses `--root` before the subcommand and writes durable entries to `learning/memory_tree/chunks.db` instead of `learnings/` directly.
- `log-learning`, `log-error`, `log-feature`, and `log-correction` are new specific commands; the old `log` subcommand is preserved for compatibility.

### From `self-improving-compound` (original)

- Data was previously at `~/self-improving/`. Now it lives at `<workspace-root>/learning/`.
- The script no longer hard-codes `~/self-improving`. Use `--root` or `OPENCLAW_WORKSPACE` to set your preferred location.
- Legacy `memory.md` and `corrections.md` bootstrap files have been removed. All entries live in SQLite. Use `export` or `index.md` for human-readable views.

### From `self-improving-agent-local`

- The old `learnings/LEARNINGS.md`, `learnings/ERRORS.md`, `learnings/FEATURE_REQUESTS.md` structure can coexist, but the hybrid skill prefers SQLite-backed `learning/memory_tree/chunks.db` plus markdown export.
- Promotion targets (`CLAUDE.md`, `AGENTS.md`, `SOUL.md`, `TOOLS.md`) remain the same.

## Safety

- Never log secrets, tokens, or private data. The CLI performs best-effort redaction.
- Corrections use table format for easy scanning.
- All entries have unique IDs for traceability.
- `search-before-log` deduplication prevents noise.

## License

MIT — feel free to fork and adapt for your own agent.

## Author

Rockway Chen · [rockwaychen@gmail.com](mailto:rockwaychen@gmail.com) · [GitHub: LingmaFuture](https://github.com/LingmaFuture)

