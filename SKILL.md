---
name: self-improvement
description: "Capture durable lessons from debugging, user corrections, missing capabilities, and repeated workflow friction so future sessions avoid the same mistakes. Hybrid design: actual-self-improvement execution core + self-improving-compound HOT/WARM/COLD memory tiers + legacy promotion/hook guidance. Use when a non-obvious failure is diagnosed, the user corrects or updates the agent, a workaround or project convention is discovered, a capability is missing, a solved issue should be promoted into shared memory, or you should review prior learnings before changing a known-problem area. Do not use for trivial typos, expected failures, straightforward retries, or one-off noise with no reusable lesson."
compatibility: "Portable Agent Skills format. Core workflow is agent-agnostic. Bundled helpers require Python 3.9+; hook helpers require bash. No network access is required."
metadata:
  version: "5.0.0"
  original_slug: "self-improving-compound"
  category: "workflow"
  author: "Hybrid adaptation from actual-self-improvement and self-improving-compound"
---

# Self-Improvement

Capture, review, promote, and extract durable lessons so future sessions avoid repeating the same mistakes.

## Core idea

Use this skill for **reusable learning**, not for every bump in the road.

A good entry usually has at least one of these properties:
- It corrected a wrong assumption.
- It revealed a project-specific convention.
- It required real debugging or investigation.
- It is likely to recur.
- It should change future workflow, memory, or tooling.

Do **not** log routine noise such as obvious typos, expected validation failures, or errors that were solved immediately with no transferable lesson.

## Hybrid architecture

This skill merges three design lineages into one portable package:

| Lineage | Role | What We Kept |
|---|---|---|
| **actual-self-improvement** | Execution core | Python CLI (`scripts/learnings.py`), structured logging, JSON evals, search-before-log dedupe |
| **self-improving-compound** | Memory architecture | HOT/WARM/COLD tiers (`memory.md`, `projects/`, `domains/`, `archive/`), `corrections.md` quick table, `index.md` auto-index |
| **self-improving-agent-local** | Promotion & hooks | Quantified promotion thresholds, OpenClaw hook guidance, pattern-key recurrence rules |

### Directory layout under `.learnings/self-improving/`

```
.learnings/self-improving/
├── memory.md              # HOT tier (always loaded)
├── corrections.md         # Structured correction log (quick table)
├── index.md               # Auto-maintained index + Pattern-Key index
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
   - `.learnings/self-improving/memory.md`
   - `.learnings/self-improving/corrections.md`
   - `.learnings/self-improving/index.md`
   - `.learnings/self-improving/projects/`
   - `.learnings/self-improving/domains/`
   - `.learnings/self-improving/archive/`
   - `CLAUDE.md`, `AGENTS.md`, `.github/copilot-instructions.md`, `SOUL.md`, `TOOLS.md`

Never write learnings into the installed skill directory. Always target the **workspace root**.

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

Before reading or writing `.learnings/self-improving/`, determine `WORKSPACE_ROOT`.

Good defaults:
- the repository root for the current codebase
- the OpenClaw workspace root (`OPENCLAW_WORKSPACE` env var)
- the directory containing the files being edited

If unsure, prefer the directory containing `.git`, `AGENTS.md`, `CLAUDE.md`, or the user's active project files.

### 2) Initialise `.learnings/self-improving/` if needed

Use the helper instead of creating files manually:

```bash
python3 scripts/learnings.py --root /absolute/path/to/workspace init
```

This creates:
- `.learnings/self-improving/memory.md`
- `.learnings/self-improving/corrections.md`
- `.learnings/self-improving/index.md`
- `.learnings/self-improving/projects/`
- `.learnings/self-improving/domains/`
- `.learnings/self-improving/archive/`

### 3) Review existing learnings before risky or familiar work

Review first when:
- you are returning to an area with prior failures
- the task touches infra, CI, deployment, auth, data migration, or generated code
- the user explicitly says "remember this", "we hit this before", or similar

Use the helper:

```bash
python3 scripts/learnings.py --root /absolute/path/to/workspace status
python3 scripts/learnings.py --root /absolute/path/to/workspace search "pnpm" --limit 5
```

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
Use for user corrections and updated facts. Written to `corrections.md` as a quick-scan table row.

```bash
python3 scripts/learnings.py --root /absolute/path/to/workspace log-correction \
  --summary "Used wrong format for Telegram" \
  --correct "Use lists, not tables" \
  --pattern telegram-format
```

#### Learning
Use for corrections, knowledge gaps, best practices, and durable conventions. Written to `memory.md`.

```bash
python3 scripts/learnings.py --root /absolute/path/to/workspace log-learning \
  --summary "Project uses pnpm workspaces, not npm" \
  --details "Attempted npm install. Lockfile and workspace config showed pnpm." \
  --pattern pnpm-workspace
```

#### Error
Use for non-obvious failures, exceptions, or tool/API issues worth remembering. Written to `memory.md`.

```bash
python3 scripts/learnings.py --root /absolute/path/to/workspace log-error \
  --summary "Docker build failed on Apple Silicon due to platform mismatch" \
  --details "docker build -t myapp . on Apple Silicon" \
  --pattern docker-platform
```

#### Feature request
Use when the user wants a missing capability or a recurring friction point should become a feature. Written to `memory.md`.

```bash
python3 scripts/learnings.py --root /absolute/path/to/workspace log-feature \
  --summary "User needs report export to CSV" \
  --details "Needed for sharing weekly reports with non-technical stakeholders" \
  --pattern csv-export
```

#### Backward-compatible log
The old `log` subcommand is preserved for compatibility:

```bash
python3 scripts/learnings.py --root /absolute/path/to/workspace log "Used wrong format" \
  --type COR --pattern telegram-format --correct "Use lists" --force
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

## Promotion thresholds (from legacy)

| Condition | Threshold | Action |
|---|---|---|
| HOT -> WARM | 30 days unused | Move to `domains/` or `projects/` |
| WARM -> COLD | 90 days unused | Move to `archive/` |
| WARM -> HOT | 3 uses within 7 days | Move to `memory.md` |
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
- entries are created with deterministic IDs and consistent fields
- repeated issues link to each other instead of fragmenting
- proven rules move into persistent memory files
- broadly useful fixes become standalone skills
- the skill itself is tested with trigger and output evals in `evals/`
