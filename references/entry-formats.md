# Entry formats

Use the bundled `scripts/learnings.py` when possible. These templates are the manual fallback.

## Correction entry

Written to `corrections.md` as a table row:

```markdown
| COR-YYYYMMDD-XXX | YYYY-MM-DD | pattern-key | What I got wrong | Correct answer | ⏳ pending |
```

## Learning entry

Written to `memory.md`:

```markdown
### LRN-YYYYMMDD-XXX (YYYY-MM-DD) [Pattern-Key: stable.pattern.key]
- **Type**: LRN
- **Summary**: One-line summary of the lesson
- **Details**: What happened, what was wrong or surprising, and what is now known to be true
```

## Error entry

Written to `memory.md`:

```markdown
### ERR-YYYYMMDD-XXX (YYYY-MM-DD) [Pattern-Key: error-pattern]
- **Type**: ERR
- **Summary**: One-line description of the failure
- **Details**: Command, tool, API, or environment details
```

## Feature request entry

Written to `memory.md`:

```markdown
### FTR-YYYYMMDD-XXX (YYYY-MM-DD) [Pattern-Key: feature-pattern]
- **Type**: FTR
- **Summary**: One-line summary of the request
- **Details**: Why the capability matters and a concrete starting point
```

## Status guidance

- `pending` — captured, not yet addressed
- `in_progress` — being worked on now
- `resolved` — issue fixed or lesson integrated
- `wont_fix` — intentionally not addressing it
- `promoted` — distilled into project memory
- `promoted_to_skill` — extracted into a reusable skill
