# Self-Improving Compound

[中文说明 / Chinese README](README_zh.md)

A portable AgentSkill that turns agent memory from scattered markdown notes into a structured self-improvement system: real-time capture, SQLite-backed learning, cron audits, daily factual memory, and lightweight workspace stewardship.

## What it does

- **Captures durable lessons** before the final reply after non-trivial work: user corrections, tool/API gotchas, non-obvious failures, workarounds, and missing capabilities.
- **Stores execution learnings in SQLite** under `learning/memory_tree/chunks.db`, with search, dedupe, lifecycle status, exports, and human-readable snapshots.
- **Keeps facts separate from lessons**: factual continuity goes to `memory/YYYY-MM-DD.md`; reusable prevention rules go to `learning/`.
- **Audits itself with cron**: light checks, heavy audits, daily factual memory, and post-digest workspace stewardship.
- **Promotes stable rules** into the right layer: `skills/`, `AGENTS.md`, `TOOLS.md`, `MEMORY.md`, or other root agent state files.

## 3+7 co-evolution model

This system keeps three durable state directories and seven root Markdown control-plane files aligned:

**3 state directories**

- `memory/` — factual daily continuity: what happened, what changed, decisions, links, follow-ups.
- `learning/` — SQLite-backed execution lessons: corrections, tool/API gotchas, workflow rules.
- `skills/` — hardened reusable procedures that future agents can load on demand.

**7 root Markdown files**

- `AGENTS.md` — workspace contract, routing, execution policy, safety boundaries.
- `HEARTBEAT.md` — lightweight check-in surface; often intentionally empty when cron owns timing.
- `IDENTITY.md` — compatibility pointer or short identity bridge.
- `MEMORY.md` — pinned long-term hot context.
- `SOUL.md` — agent identity/persona.
- `TOOLS.md` — concrete local environment/tool facts.
- `USER.md` — durable user profile and collaboration preferences.

The steward loop should make only small, safe consistency updates across these files. It should not rewrite persona, weaken safety rules, or turn daily facts into root-level bloat.

## Architecture

```text
Real-time capture gate
  -> search existing SQLite learnings
  -> log compact correction/error/learning/feature entries
  -> maintain HOT/WARM/COLD lifecycle

Daily factual memory
  -> write memory/YYYY-MM-DD.md
  -> extract only reusable lessons into learning/

Workspace stewardship
  -> export learning memory
  -> inspect learning/, skills/, and the 7 root Markdown control-plane files
  -> make only small safe consistency updates
```

## Install

```bash
clawhub install self-improving-compound
```

Or copy this directory into your skills location.

Requirements:

- Python 3.8+
- bash
- No network access required for the local CLI

## Quick start

```bash
# Initialize learning storage in a workspace
python3 scripts/learnings.py --root /path/to/workspace init

# Search before logging
python3 scripts/learnings.py --root /path/to/workspace search "telegram format" --limit 5

# Log a correction
python3 scripts/learnings.py --root /path/to/workspace log-correction \
  --summary "Telegram replies should avoid wide tables" \
  --correct "Use compact lists for mobile chat" \
  --pattern chat:telegram-format

# Log a reusable learning
python3 scripts/learnings.py --root /path/to/workspace log-learning \
  --summary "Cron jobs that need conversation context must pull session history explicitly" \
  --details "Isolated cron sessions do not automatically inherit the main chat context." \
  --pattern cron:session-context

# Review and maintain lifecycle
python3 scripts/learnings.py --root /path/to/workspace status
python3 scripts/learnings.py --root /path/to/workspace maintain --apply

# Export for review
bash scripts/learning-export.sh
```

## Optional cron pipeline

The skill ships with OpenClaw cron templates in `scripts/setup-cron.json` and an agent setup guide in `scripts/setup-cron-agent.md`.

Recommended jobs:

| Job | Default schedule | Purpose |
|---|---:|---|
| Self-Improving Light Check | every 2h, 08:00–22:00 | Catch obvious missed corrections and blockers. |
| Learning Audit Heavy | 09:00 and 22:00 | Audit failures, log missed lessons, maintain lifecycle. |
| Daily Memory Digest | 23:50 | Write `memory/YYYY-MM-DD.md`, then extract reusable lessons. |
| Daily Workspace Steward | 00:20 | Export learning memory and lightly inspect `learning/`, `skills/`, and the 7 root Markdown control-plane files. |

Cron installation is not automatic. Ask your OpenClaw agent:

> Install the self-improving compound cron jobs using `scripts/setup-cron.json` as reference. Check existing cron jobs first and update instead of duplicating.

## Path model

There are two roots:

1. **Skill root** — this package: `scripts/`, `hooks/`, `references/`, `evals/`.
2. **Workspace root** — your active agent/project state:
   - `learning/memory_tree/chunks.db`
   - `learning/index.md`
   - `memory/YYYY-MM-DD.md` if daily factual memory is enabled
   - root agent files such as `AGENTS.md`, `MEMORY.md`, `TOOLS.md`, `USER.md`, `SOUL.md`, `HEARTBEAT.md`, `IDENTITY.md`

Never write durable learnings into the installed skill directory. Always pass `--root /path/to/workspace`.

## Key commands

```bash
python3 scripts/learnings.py --root /path/to/workspace init
python3 scripts/learnings.py --root /path/to/workspace status --format json
python3 scripts/learnings.py --root /path/to/workspace search "keyword" --limit 10
python3 scripts/learnings.py --root /path/to/workspace search "keyword" --touch
python3 scripts/learnings.py --root /path/to/workspace log-error --summary "..." --details "..." --pattern area:stable-key
python3 scripts/learnings.py --root /path/to/workspace log-feature --summary "..." --details "..." --pattern feature:stable-key
python3 scripts/learnings.py --root /path/to/workspace maintain --apply
python3 scripts/learnings.py --root /path/to/workspace promote LRN-YYYYMMDD-001 --to AGENTS.md
bash scripts/daily-memory.sh --root /path/to/workspace
bash scripts/extract-skill.sh my-new-skill /path/to/workspace
```

## Guardrails

- Search before logging to avoid duplicates.
- Keep entries compact, searchable, and prevention-oriented.
- Do not log secrets, tokens, raw private transcripts, or volatile state.
- Treat cron audit candidates as review prompts, not automatic truth.
- Daily Workspace Steward may make small safe markdown updates only; it must not rewrite persona, weaken safety/privacy rules, delete files, or change cron jobs.

## Included references

- `references/entry-formats.md` — schemas and manual templates
- `references/promotion-and-extraction.md` — promotion thresholds and extraction criteria
- `references/platform-setup.md` — setup guidance for multiple agent runtimes
- `references/heartbeat-guidance.md` — when to use heartbeat vs cron
- `references/daily-memory-digest.md` — daily factual memory quality bar
- `references/hermes-integration.md` — architecture concepts absorbed from Hermes-style agents

## Credits

Hybrid adaptation from actual-self-improvement, self-improving-compound, OpenHuman memory-tree, local self-improving-agent patterns, GenericAgent memory hygiene axioms, and Hermes-style agent architecture.

Author/maintainer: Rockway Chen · <rockwaychen@gmail.com> · <https://github.com/LingmaFuture>
