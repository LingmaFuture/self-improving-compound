# Changelog

All notable changes to this project will be documented in this file.

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
- `scripts/learnings.py` no longer hard-codes `~/self-improving`. All data now lives under `<root>/.learnings/self-improving/`.
- `hooks/activator.sh` and `hooks/error-detector.sh` are now workspace-root aware and use `OPENCLAW_WORKSPACE`.
- `index.md` now includes tier statistics and Pattern-Key index.

### Deprecated
- Backward-compatible `log CONTENT --type ...` command is preserved but specific `log-*` commands are preferred.

### Removed
- Hard-coded `BASE_DIR = Path.home() / "self-improving"` from `scripts/learnings.py`.
- Markdown eval checklists replaced with JSON evals.
