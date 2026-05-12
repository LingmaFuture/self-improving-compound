# Self-Improving Compound

A composite self-improving skill for OpenClaw that absorbs the best practices from major self-improving agent frameworks:

- **OpenClaw stock** (v1.2.16) — the built-in HOT/WARM/COLD tiered architecture
- **tristanmanchester/actual-self-improvement** — Python toolchains, structured logging, JSON evals
- **pskoett/self-improving-agent** — quantified promotion thresholds, OpenClaw hooks, pattern-key recurrence rules
- **GenericAgent** (MIT) — memory hygiene axioms: action-verified memory, volatile-state avoidance, pointer/index hygiene

## Architecture

This is a **hybrid design**: actual-self-improvement serves as the execution core, while self-improving-compound provides the memory architecture, and the local agent lineage contributes promotion rules and hook guidance.

### Skill root (bundled resources)

```
.
├── SKILL.md                          # Portable AgentSkill frontmatter + rules
├── scripts/
│   ├── learnings.py                  # CLI: init, status, search, log, log-*, promote, edit, maintain
│   ├── extract-skill.sh              # Extract reusable skill from learnings
│   └── daily-memory.sh               # Generate comprehensive daily memory entries
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
└── learning/self-improving/
    ├── memory.md              # HOT tier (always loaded)
    ├── corrections.md         # Structured correction log (quick table)
    │   │   ├── index.md               # Auto-maintained index + Pattern-Key index + Skill Registry + Skill Registry
    ├── projects/              # WARM tier (project-specific)
    ├── domains/               # WARM tier (domain-specific)
    └── archive/               # COLD tier (inactive)
```

## Install

### As a portable AgentSkill

1. Copy or symlink this directory into your skills location:
   ```bash
   cp -r self-improving-compound ~/.openclaw/skills/self-improvement
   ```

2. Ensure `scripts/learnings.py` is executable:
   ```bash
   chmod +x scripts/learnings.py scripts/extract-skill.sh hooks/*.sh
   ```

### Requirements

- Python 3.9+
- bash (for hook scripts)
- No network access required

## Quick Start

```bash
# 1. Initialize structure in a workspace
python3 scripts/learnings.py --root /path/to/workspace init

# 2. Log a correction
python3 scripts/learnings.py --root /path/to/workspace log-correction \
  --summary "Used wrong format for Telegram" \
  --correct "Use lists, not tables" \
  --pattern telegram-format

# 3. Log a learning
python3 scripts/learnings.py --root /path/to/workspace log-learning \
  --summary "Always search before logging" \
  --details "Avoid duplicate long-term memory entries" \
  --pattern dedup-rule

# 4. Search
python3 scripts/learnings.py --root /path/to/workspace search "telegram"
python3 scripts/learnings.py --root /path/to/workspace search "telegram" --format json

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

# 10. Generate comprehensive daily memory
bash scripts/daily-memory.sh /path/to/workspace
```

`--root` can be placed either before the subcommand (global) or after it (command-local). Both forms are supported.

## Path model

There are **two different roots**:

1. **Skill root** — where this repository lives (scripts, references, hooks).
2. **Workspace root** — where `learning/self-improving/` is created and written.

Never write learnings into the skill directory. Always target the workspace root.

The workspace root is resolved in this order:
1. `--root /path/to/workspace` (explicit, either before or after the subcommand)
2. `OPENCLAW_WORKSPACE` environment variable
3. Current working directory

Dates and IDs use the system local timezone by default. Set `SOURCE_DATE_EPOCH` for reproducible builds.

## Key Features Absorbed

| Source | Feature | How It's Integrated |
|--------|---------|---------------------|
| **stock** | HOT/WARM/COLD tiers | Native directory structure under `learning/self-improving/` |
| **stock** | Automatic promotion (30d/90d) | Enforced by `maintain` command with `--dry-run` and `--apply`; moves stale entries (not whole files) to preserve unrelated content |
| **stock** | Namespace isolation (projects/domains/archive) | Native directory structure |
| **tristanmanchester** | `learnings.py` CLI | Adapted to hybrid directory layout with `--root` support |
| **tristanmanchester** | `extract_skill.py` | Simplified to bash + scaffold |
| **tristanmanchester** | Evals framework | JSON evals: `trigger-validation.json` + `output-evals.json` |
| **tristanmanchester** | Pattern-Key stable identifiers | Built into logging commands and auto-index |
| **pskoett** | `TYPE-YYYYMMDD-XXX` ID format | Auto-generated by `learnings.py` |
| **pskoett** | Quantified promotion threshold | `Recurrence-Count >= 3 + 2+ tasks + 30d` |
| **pskoett** | Hooks (activator + error-detector) | Simplified bash versions, workspace-root aware |
| **GenericAgent** | Memory hygiene (action-verified, no volatile state, pointer hygiene) | Rules in `references/promotion-and-extraction.md`, validation in `scripts/learnings.py` |
| **ivangdavila** | Human-like memory lifecycle | `maintain` subcommand with promotion/demotion/archive |
| **ivangdavila** | HOT/WARM/COLD limits & namespace specificity | Tier enforcement + `project > domain > global` conflict resolution |
| **ivangdavila** | Compaction by summarization/merge | `maintain` merges/summarizes; never deletes confirmed preferences |
| **ivangdavila** | Heartbeat maintenance guidance | `references/heartbeat-guidance.md` with periodic `maintain --dry-run` |
| **ivangdavila** | Transparent source/pointer hygiene | Metadata fields + citation-ready entries |

## Memory Lifecycle

This skill integrates a human-like memory lifecycle inspired by `ivangdavila/self-improving`:

| Tier | Location | Trigger | Behavior |
|------|----------|---------|----------|
| **HOT** | `memory.md`, `corrections.md` | Active use | Always loaded; entries include `First-Seen`, `Last-Seen`, `Recurrence-Count`, `Status`, and `Area` metadata |
| **WARM** | `projects/`, `domains/` | Demoted from HOT after 30 days unused | Load on context match; preserves full history |
| **COLD** | `archive/` | Demoted from WARM after 90 days unused | Load on explicit query; never deleted without explicit action |

### Automatic lifecycle rules

The `maintain` command enforces these rules safely:

| Condition | Threshold | Action |
|-----------|-----------|--------|
| HOT -> WARM | 30 days unused | Move stale entry to appropriate `domains/` or `projects/` file based on `Area` metadata |
| WARM -> COLD | 90 days unused | Move stale entry to `archive/<source-name>.md` |
| WARM -> HOT | `Recurrence-Count >= 3` or 3 uses within 7 days | Flag for promotion back to `memory.md` |
| Compaction | File exceeds tier limit | Merge or summarize; never erase confirmed preferences |

### Conflict resolution

When patterns contradict, the following precedence applies:

1. **More specific wins**: `project` > `domain` > `global`
2. **More recent wins** at the same specificity level
3. **Ambiguous conflicts** require asking the user instead of guessing

### Maintenance safety

- `maintain` defaults to `--dry-run`; use `--apply` to execute moves.
- Content is never deleted; it is moved, archived, or summarized.
- If metadata is insufficient, `maintain` reports recommendations rather than making destructive guesses.
- The heartbeat guidance (see `references/heartbeat-guidance.md`) suggests running `maintain --dry-run` periodically.

## Promotion Rules

| Tier | Condition | Action |
|------|-----------|--------|
| HOT -> WARM | 30 days unused | Move stale entry to `domains/` or `projects/` based on `Area` metadata |
| WARM -> COLD | 90 days unused | Move stale entry to `archive/<source-name>.md` |
| WARM -> HOT | 3 uses within 7 days | Move to `memory.md` |
| To AGENTS/SOUL/TOOLS | Proven + broadly applicable | Promote as short prevention rule |
| To skill | Proven + broadly applicable | Extract as skill |

## Migration from prior versions

### From `actual-self-improvement`

- Move existing `learnings/LEARNINGS.md`, `learnings/ERRORS.md`, `learnings/FEATURE_REQUESTS.md` into `learning/self-improving/` if desired, or keep them alongside.
- The CLI now uses `--root` before the subcommand and writes to `learning/self-improving/` instead of `learnings/` directly.
- `log-learning`, `log-error`, `log-feature`, and `log-correction` are new specific commands; the old `log` subcommand is preserved for compatibility.

### From `self-improving-compound` (original)

- Data was previously at `~/self-improving/`. Now it lives at `<workspace-root>/learning/self-improving/`.
- The script no longer hard-codes `~/self-improving`. Use `--root` or `OPENCLAW_WORKSPACE` to set your preferred location.
- `corrections.md` and `memory.md` formats are preserved; `index.md` is still auto-maintained.

### From `self-improving-agent-local`

- The old `learnings/LEARNINGS.md`, `learnings/ERRORS.md`, `learnings/FEATURE_REQUESTS.md` structure can coexist, but the hybrid skill prefers the unified `memory.md` + `corrections.md` layout.
- Promotion targets (`CLAUDE.md`, `AGENTS.md`, `SOUL.md`, `TOOLS.md`) remain the same.

## Safety

- Never log secrets, tokens, or private data. The CLI performs best-effort redaction.
- Corrections use table format for easy scanning.
- All entries have unique IDs for traceability.
- `search-before-log` deduplication prevents noise.

## License

MIT — feel free to fork and adapt for your own agent.
