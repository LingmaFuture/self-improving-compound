# Memory (HOT Tier)

## ID Rules
- All entries use format: `TYPE-YYYYMMDD-XXX` (e.g., COR-20260508-001)
- Types: COR (correction), LRN (learning), FTR (feature), ERR (error)

## Pattern-Key Rules
- Recurring issues get a stable Pattern-Key (e.g., `markdown-table-telegram`)
- Link related entries with `See Also: [Pattern-Key]`
- Bump priority when Recurrence-Count >= 3 + spans 2+ tasks + within 30 days

## Promotion Thresholds
- HOT -> WARM: 30 days unused
- WARM -> COLD: 90 days unused
- WARM -> HOT: 3 uses within 7 days
- To AGENTS.md/SOUL.md/TOOLS.md: proven + broadly applicable

## Preferences
<!-- Add your personal preferences here -->

## Patterns
<!-- Add recurring patterns here -->

## Rules
- Self-improving skill mode: Passive.
- Use `python3 ~/self-improving/scripts/learnings.py` for logging/search/status.
- Search before log to avoid duplicates.
