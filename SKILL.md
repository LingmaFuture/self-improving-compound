---
name: self-improving-compound
description: "Agent memory and self-improvement system. Replaces naive file-based agent memory with a structured SQLite learning engine: capture corrections, errors, and reusable lessons during active work, audit session history for missed learnings via isolated cron jobs, and promote proven rules into skills and agent instructions. 7+3 co-evolution model — memory/ (facts), learning/ (SQLite lessons), skills/ (hardened rules), AGENTS.md (behavior), TOOLS.md (env knowledge), MEMORY.md (long-term context), HEARTBEAT.md (check-ins) all improve together. Python 3.8+ CLI with bash hooks. Use for: logging non-obvious failures, user corrections, tool/API gotchas, or missing capabilities before the final reply. Use for: setting up automated cron-based audit pipelines that catch what real-time capture misses. Do not use for trivial typos or routine noise."
compatibility: "Portable Agent Skills format. Core workflow is agent-agnostic. Bundled helpers require Python 3.8+; hook helpers require bash. No network access is required."
metadata:
  version: "6.1.6"
  original_slug: "self-improving-compound"
  category: "memory-system"
  author: "Hybrid adaptation from actual-self-improvement, self-improving-compound, OpenHuman memory-tree, and Hermes Agent architecture | Contact: rockwaychen@gmail.com | GitHub: LingmaFuture"
---

# Self-Improving Compound

An agent memory and learning system that replaces naive file-based memory with a structured pipeline: real-time capture, automated cron-based audit, and continuous promotion of lessons into skills and agent instructions.

The system runs as three layers:
- **Layer 1 — Real-time capture**: AGENTS.md final-before-reply gate logs corrections, errors, and workarounds to SQLite as they happen.
- **Layer 2 — Cron audit**: Isolated background jobs scan session history via `sessions_history`, detect missed lessons, and maintain lifecycle (HOT → WARM → COLD).
- **Layer 3 — Promotion**: Proven rules flow from `learning/` SQLite → `skills/` SKILL.md → `AGENTS.md` → `TOOLS.md`. The full 7+3 system co-evolves.

**Author:** Rockway Chen · [rockwaychen@gmail.com](mailto:rockwaychen@gmail.com) · [GitHub: LingmaFuture](https://github.com/LingmaFuture)

## Core idea

Use this system for **durable improvement**, not for every bump in the road.

### Mandatory capture gate

Before a final reply, run this quick check:

- Did the task include a non-obvious failure, API/tool quirk, or format mismatch?
- Did a workaround or environment-specific convention make the task succeed?
- Did the user correct a fact, preference, workflow, or expectation?
- Would repeating this lesson save time or prevent damage later?

If yes, **search existing learnings first, then log the lesson before replying**. Do not rely on a “mental note.”

A good entry usually has at least one of these properties:
- It corrected a wrong assumption.
- It revealed a project-specific convention.
- It required real debugging or investigation.
- It is likely to recur.
- It should change future workflow, memory, or tooling.

Do **not** log routine noise such as obvious typos, expected validation failures, or errors that were solved immediately with no transferable lesson.

### Capture gate output routing

Not all lessons go to the same place. Route based on type:

| Lesson type | Destination | Example |
|---|---|---|
| User facts, preferences, system state | `MEMORY.md` / `memory/YYYY-MM-DD.md` | "Rockway prefers newspaper theme" |
| Execution mistakes, tool gotchas, workarounds | `learning/` SQLite | "Python shadowing broke promote" |
| Stable rules, workflows, anti-patterns discovered | owning `skills/<skill>/SKILL.md` | "cron isolation means no session context" |
| Behavioral constraints | `AGENTS.md` | "Don't commit workspace root" |
| Environment-specific tool knowledge | `TOOLS.md` | "Tailscale node name" |

The full system co-evolves: fixing one layer while leaving another stale is half-done work. When a lesson reveals a skill is stale, upgrade it immediately and bump its version.

## Hybrid architecture

This skill merges three design lineages into one portable package:

| Lineage | Role | What We Kept |
|---|---|---|
| **actual-self-improvement** | Execution core | Python CLI (`scripts/learnings.py`), structured logging, JSON evals, search-before-log dedupe |
| **OpenHuman memory-tree** | Storage core | SQLite chunks, entity index, scores, hotness, lifecycle status, idempotent ingest |
| **self-improving-compound** | Memory architecture | HOT/WARM/COLD lifecycle, workspace-scoped `learning/`, lightweight bootstrap markdown |
| **self-improving-agent-local** | Promotion & hooks | Quantified promotion thresholds, OpenClaw hook guidance, pattern-key recurrence rules |

### Directory layout under `learning/`

```
learning/
├── memory_tree/chunks.db  # SQLite source of truth for durable learnings
├── index.md               # SQLite-generated snapshot (entries, lifecycle, pattern keys)
├── projects/              # WARM tier (project-specific)
├── domains/               # WARM tier (domain-specific)
└── archive/               # COLD tier (inactive)
```

## Important path model

There are **two different roots** in this skill:

1. **Skill root** — where bundled resources live:
   - `scripts/...`
   - `references/...`
   - `hooks/...`

2. **Workspace root** — where the project or active workspace lives:
- `learning/memory_tree/chunks.db`
- `learning/index.md` (SQLite-generated snapshot)
- `learning/projects/`
- `learning/domains/`
- `learning/archive/`
   - `CLAUDE.md`, `AGENTS.md`, `.github/copilot-instructions.md`, `SOUL.md`, `TOOLS.md`

Never write learnings into the installed skill directory. Always target the **workspace root**.


## Activation hardening mechanisms

When this skill is installed in a persistent agent runtime, self-improvement must be enforced by the system rather than left to memory. The recommended architecture uses two layers:

- **Layer 1 — Capture gate**: an agent instruction requiring `search + log` before every final reply after a non-trivial task. This catches lessons in real-time during active work.
- **Layer 2 — Cron enforcement**: isolated background jobs that audit recent session history, scan for system failures, maintain lifecycle, and export SQLite for review. Cron runs in *isolated sessions* that do not consume the main conversation context.

### Architecture decisions (why cron, not heartbeat)

- **Cron is isolated.** `sessionTarget: "isolated"` creates a fresh ephemeral session that does not pollute the main agent's context window or bust prompt-cache warmth.
- **Cron has tool access to main session history.** Use `sessions_list` to locate the active main session, then `sessions_history` to pull recent assistant turns. This gives the cron job visibility into real conversation without running inside the main session.
- **Heartbeat runs in the main session by default.** Its role should be limited to lightweight check-ins and urgent reminders. Do not embed audit execution commands in `HEARTBEAT.md`; keep that file minimal so heartbeat returns `HEARTBEAT_OK` quickly unless an urgent decision is needed.

### Recommended cron schedule

```text
Cron                                     Schedule (Asia/Shanghai)
──────────────────────────────────────   ──────────────────────
Self-Improving Light Check               0 8-22/2 * * *    (every 2h during waking hours)
Learning Audit (Heavy)                   0 9,22 * * *      (2x/day)
Daily Learning Export                    10 0 * * *        (once/day after midnight)
```

#### Light Check (every 2h, 08:00-22:00)

A quick in-between scan that locates the main session via `sessions_list`, pulls recent assistant turns via `sessions_history`, and checks whether any user correction, non-obvious error, workaround, or tool/API quirk has been missed by the SQLite learning store. Tools: `sessions_list`, `sessions_history`, `exec` (for `learnings.py search`), `read`. Timeout: 120-180s.

#### Heavy Audit (09:00, 22:00)

Full audit: system-failure check, cron-failure scan, `learning-audit.py --log`, and `learnings.py maintain --apply` for lifecycle promotion/demotion. Tools: `exec`, `read`, `cron`. Timeout: 240s.

#### Daily Export (00:10)

Run `scripts/learning-export.sh` to write `learning/memory-export.md` and `learning/status.json` for human review. Tools: `exec`, `read`. Timeout: 120s.

### AGENTS.md capture gate

Add the following rule to agent instructions (e.g. AGENTS.md):

> Before every final reply after a non-trivial task: if the task involved a user correction, non-obvious failure, API/tool quirk, workaround, format mismatch, missing capability, or reusable convention, search existing SQLite learning first with `scripts/learnings.py --root <workspace> search "<keywords>" --limit 5`. If no suitable entry exists, log the durable lesson before replying. Never rely on a mental note; `learning/memory_tree/chunks.db` is the execution-learning source of truth.

### System failure routing

Route watchdog, doctor, healthcheck, and cron failure signals into `log-error` with stable pattern keys and dedupe:

- Pattern keys: `cron:<job-name>`, `doctor:<check-name>`, `watchdog:<component>`, `system:openclaw-audit-failure`
- Use `scripts/log-system-failures.sh` as an OpenClaw CLI audit wrapper where available.
- Always search existing entries first to prevent repeated failures from flooding SQLite.

### Guardrails

- Keep entries compact and prevention-oriented.
- Never log secrets; the CLI redacts tokens, passwords, and API keys automatically.
- Do not paste full audit exports into chat unless explicitly asked.
- Treat audit candidates as review prompts rather than automatic truth.
- Cron runs should reply with one-line summaries or `HEARTBEAT_OK`; do not echo full command output.

## Quick decision table

| Situation | What to do |
|---|---|
| User corrects you or updates a fact | Log a **correction** |
| Non-obvious command / API / tool failure | Log an **error** |
| User asks for a missing capability | Log a **feature request** |
| You discover a reusable workaround or convention | Log a **learning** |
| A pattern keeps recurring | Search related entries, link with `See Also`, and consider promotion |
| A lesson is broadly applicable or repeated | Promote it into project memory |
| A resolved, general pattern could help other projects | Extract a new skill |

## Standard workflow

### 1) Find the workspace root first

Before reading or writing `learning/`, determine `WORKSPACE_ROOT`.

Good defaults:
- the repository root for the current codebase
- the OpenClaw workspace root (`OPENCLAW_WORKSPACE` env var)
- the directory containing the files being edited

If unsure, prefer the directory containing `.git`, `AGENTS.md`, `CLAUDE.md`, or the user's active project files.

### 2) Initialise `learning/` if needed

Use the helper instead of creating files manually:

```bash
python3 scripts/learnings.py --root /absolute/path/to/workspace init
```

This creates:
- `learning/memory_tree/chunks.db` (SQLite database)
- `learning/projects/`
- `learning/domains/`
- `learning/archive/`

The `learning/index.md` snapshot is generated on first write (log, promote, etc.).

### 3) Review existing learnings before risky or familiar work

Review first when:
- you are returning to an area with prior failures
- the task touches infra, CI, deployment, auth, data migration, or generated code
- the user explicitly says "remember this", "we hit this before", or similar

Use the helper:

```bash
python3 scripts/learnings.py --root /absolute/path/to/workspace status
python3 scripts/learnings.py --root /absolute/path/to/workspace search "pnpm" --limit 5
python3 scripts/learnings.py --root /absolute/path/to/workspace search "pnpm" --touch

# --root can also be placed after the subcommand
python3 scripts/learnings.py status --root /absolute/path/to/workspace --format json
```

Plain `search` is read-only. Use `--touch` only when the result was actually reused and should increment recurrence metadata.

### 4) Search before logging to avoid duplicates

Always search for related entries before creating a new one.

```bash
python3 scripts/learnings.py --root /absolute/path/to/workspace search "keyword or pattern" --limit 10
```

If a similar entry already exists:
- prefer linking with `See Also`
- reuse or add a stable `Pattern-Key` for recurring issues
- bump priority only when recurrence justifies it
- prefer updating the existing pattern story over spraying near-duplicate entries

### 5) Log the right kind of entry

#### Correction
Use for user corrections and updated facts. Stored in SQLite with a human ID such as `COR-YYYYMMDD-001`.

```bash
python3 scripts/learnings.py --root /absolute/path/to/workspace log-correction \
  --summary "Used wrong format for Telegram" \
  --correct "Use lists, not tables" \
  --pattern chat:telegram-format
```

#### Learning
Use for corrections, knowledge gaps, best practices, and durable conventions. Stored in SQLite with a human ID such as `LRN-YYYYMMDD-001`.

```bash
python3 scripts/learnings.py --root /absolute/path/to/workspace log-learning \
  --summary "Project uses pnpm workspaces, not npm" \
  --details "Attempted npm install. Lockfile and workspace config showed pnpm." \
  --pattern pkg:pnpm-workspace
```

#### Error
Use for non-obvious failures, exceptions, or tool/API issues worth remembering. Stored in SQLite with a human ID such as `ERR-YYYYMMDD-001`.

```bash
python3 scripts/learnings.py --root /absolute/path/to/workspace log-error \
  --summary "Docker build failed on Apple Silicon due to platform mismatch" \
  --details "docker build -t myapp . on Apple Silicon" \
  --pattern docker:platform
```

#### Feature request
Use when the user wants a missing capability or a recurring friction point should become a feature. Stored in SQLite with a human ID such as `FTR-YYYYMMDD-001`.

```bash
python3 scripts/learnings.py --root /absolute/path/to/workspace log-feature \
  --summary "User needs report export to CSV" \
  --details "Needed for sharing weekly reports with non-technical stakeholders" \
  --pattern reports:csv-export
```

#### Backward-compatible log
The old `log` subcommand is preserved for compatibility:

```bash
python3 scripts/learnings.py --root /absolute/path/to/workspace log "Used wrong format" \
  --type COR --pattern chat:telegram-format --correct "Use lists" --force
```

To inspect or share entries, export from SQLite:

```bash
python3 scripts/learnings.py --root /absolute/path/to/workspace export
python3 scripts/learnings.py --root /absolute/path/to/workspace export --format json
```

### 6) Promote proven lessons into memory

Promote when the learning is broad, repeated, or something any future contributor should know.

Common targets:
- `CLAUDE.md` — durable project facts and conventions
- `AGENTS.md` — workflow rules and automation guidance
- `.github/copilot-instructions.md` — shared Copilot context
- `SOUL.md` — behavioural principles in OpenClaw workspaces
- `TOOLS.md` — tool-specific gotchas in OpenClaw workspaces

Write promotions as **short prevention rules**, not long incident write-ups.

Example:
- Bad promotion: "On 2026-03-12 npm failed because…"
- Good promotion: "Use `pnpm install` in this repo; it is a pnpm workspace."

When a learning is promoted, update the original entry's status to `promoted` or `promoted_to_skill` and record the destination.

### 7) Extract a reusable skill when the pattern is real

Extract a new skill when the solution is:
- resolved and working
- broadly useful beyond one file or repo
- non-obvious enough that future agents would benefit
- recurring enough to justify its own instructions

Use the helper:

```bash
bash scripts/extract-skill.sh my-skill-name /absolute/path/to/workspace
```

## Logging rules that matter most

1. **Search first.** Duplicate entries are worse than missing tags.
2. **Prefer durable lessons.** Only log what should change future behaviour.
3. **Be specific.** Name the assumption, failure, or convention clearly.
4. **Include the fix or prevention rule.** An entry without next action is weak.
5. **Use stable pattern keys for recurring problems.** This lets recurrence compound.
6. **Promote aggressively once a rule is proven.** The point is fewer repeat mistakes.
7. **Do not interrupt the user with bookkeeping.** Log silently unless the user asked to see it or you need missing details.
8. **Never log secrets.** Tokens, passwords, API keys, and private data must be redacted or omitted.

## Memory lifecycle (integrated from ivangdavila/self-improving)

Entries carry metadata (`First-Seen`, `Last-Seen`, `Recurrence-Count`, `Status`, `Area`) so the system can make deterministic lifecycle decisions without guessing.

| Tier | Location | Size guidance | Behavior |
|------|----------|---------------|----------|
| HOT | SQLite lifecycle `admitted` | Active working set | Shown by `status`, `search`, and hooks |
| WARM | SQLite lifecycle `buffered` | 30+ days unused | Retained for context-specific search |
| COLD | SQLite lifecycle `sealed` | archived/promoted/resolved | Retained for explicit query/export |

### Automatic promotion/demotion

Use `python3 scripts/learnings.py --root <workspace> maintain` to review:

| Condition | Threshold | Action |
|---|---|---|
| HOT -> WARM | 30 days unused | Set lifecycle to `buffered` |
| WARM -> COLD | 90 days unused | Set lifecycle to `sealed` |
| Frequent reuse | `Recurrence-Count >= 3` from explicit reuse (`search --touch` or `edit`) | Flag for project-memory promotion |
| Compaction/export | Human review needed | Export and manually summarize/promote without deleting the SQLite record |

`maintain` defaults to `--dry-run`. Use `--apply` to execute lifecycle status moves. It never deletes content and does not auto-summarize.

### Conflict resolution

When patterns contradict:
1. **More specific wins**: `project` > `domain` > `global`
2. **More recent wins** at the same specificity level
3. **Ambiguous conflicts** → ask the user instead of guessing

## Promotion thresholds (from legacy)

| Condition | Threshold | Action |
|---|---|---|
| HOT -> WARM | 30 days unused | Mark `buffered` |
| WARM -> COLD | 90 days unused | Mark `sealed` |
| Frequent reuse | 3 recorded uses within 7 days | Promote as a short prevention rule |
| To AGENTS/SOUL/TOOLS | `Recurrence-Count >= 3` + spans 2+ tasks + within 30 days | Promote as short prevention rule |
| To skill | Proven + broadly applicable | Extract as skill |

## Recommended references

Use these only when needed:
- `references/entry-formats.md` — full field schemas and manual templates
- `references/promotion-and-extraction.md` — promotion rules and skill extraction criteria
- `references/platform-setup.md` — Claude Code, Codex, Copilot, and OpenClaw setup notes

## Hooks

Hook helpers are intentionally optional and workspace-root aware.

Available hook scripts:
- `hooks/activator.sh` — lightweight reminder at prompt start
- `hooks/error-detector.sh` — lightweight error reminder after failed Bash-like commands

Hook configuration examples live in `references/platform-setup.md`.

## What "next-level" looks like for this skill

A mature use of this skill has a loop:

**capture → dedupe → promote → extract → evaluate**

That means:
- entries are created with stable human IDs, content-addressed chunk IDs, and consistent fields
- repeated issues link to each other instead of fragmenting
- proven rules move into persistent memory files
- broadly useful fixes become standalone skills
- the skill itself is tested with trigger and output evals in `evals/`
