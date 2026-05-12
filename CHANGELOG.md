# Changelog

All notable changes to this project will be documented in this file.

## [6.0.0] - 2026-05-12

### Added
- **`.learnings/` directory renamed to `learnings/`** (no dot prefix) — all paths updated across scripts, hooks, docs, and evals.
- **`--area` parameter** for all `log-*` commands — supports `project:name` and `domain:name` routing for proper tier placement.
- **Auto-increment Recurrence-Count** — search command now touches matched HOT entries, updating `Last-Seen` and incrementing `Recurrence-Count`.
- **WARM→HOT reverse promotion** — `maintain` now detects entries with `Recurrence-Count >= 3` within 7 days and promotes them back to HOT tier.
- **`promote` command** (`promote ID --to FILE`) — moves entries to promotion targets (AGENTS.md, CLAUDE.md, etc.) with traceable pointers.
- **`edit` command** (`edit ID --status STATUS --last-seen DATE --recurrence N`) — updates entry metadata in-place.
- **`scripts/daily-memory.sh`** — comprehensive daily memory template generator with structured sections for sessions, decisions, errors, learnings, and self-improvement audits.
- **`references/hermes-integration.md`** — documents selectively absorbed Hermes Agent architecture concepts kept lean for this system.
- **`index.md` now includes Skill Registry** — Pattern-Key index doubles as lightweight skill discovery inspired by Hermes's Skills Hub.

### Changed
- **Dedup improved** — `_do_dedup_check()` now uses `difflib.SequenceMatcher` for semantic similarity detection (>70% threshold).
- **SKILL.md metadata** updated to reflect Hermes Agent architecture influence.
- **All paths** migrated from `.learnings/` to `learnings/` (87 references across 10 files).

### Fixed
- Recurrence-Count now auto-increments on search — no longer a static dead value.
- Promotion lifecycle is now closed-loop — WARM entries can return to HOT when frequently used.
- Missing `--area` routing fixed — WARM tier placement is now deterministic.

## [5.0.0] - 2026-05-09

### Added
- `SKILL.md` with OpenClaw/portable AgentSkill frontmatter.
- Hybrid architecture: actual-self-improvement execution core + self-improving-compound HOT/WARM/COLD memory tiers + legacy promotion/hook guidance.
- `--root PATH` global option for all CLI commands.
- `OPENCLAW_WORKSPACE` environment variable support as default root.
- New specific logging commands: `log-correction`, `log-learning`, `log-error`, `log-feature`.
- Best-effort secret redaction in logging text.
- `references/entry-formats.md`, `references/promotion-and-extraction.md`, `references/platform-setup.md`.
- Machine-readable JSON evals: `evals/trigger-validation.json` and `evals/output-evals.json`.
- `CHANGELOG.md`.

### Changed
- `scripts/learnings.py` no longer hard-codes `~/self-improving`. All data now lives under `<root>/learnings/self-improving/`.
- `hooks/activator.sh` and `hooks/error-detector.sh` are now workspace-root aware and use `OPENCLAW_WORKSPACE`.
- `index.md` now includes tier statistics and Pattern-Key index.

### Deprecated
- Backward-compatible `log CONTENT --type ...` command is preserved but specific `log-*` commands are preferred.

### Removed
- Hard-coded `BASE_DIR = Path.home() / "self-improving"` from `scripts/learnings.py`.
- Markdown eval checklists replaced with JSON evals.
