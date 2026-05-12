# Promotion and extraction

## Memory lifecycle maintenance

The `maintain` subcommand enforces the human-like memory lifecycle integrated from `ivangdavila/self-improving`.

### How `maintain` works

1. **Scan** all tiers (HOT, WARM, COLD) and parse entry metadata (`First-Seen`, `Last-Seen`, `Recurrence-Count`, `Status`, `Area`).
2. **Identify candidates**:
   - HOT entries unused for 30+ days → recommend demotion to WARM
   - WARM entries unused for 90+ days → recommend archiving to COLD
   - Entries with `Recurrence-Count >= 3` or 3 uses within 7 days → flag for promotion toward HOT
3. **Report** in human-readable text or JSON (`--format json`).
4. **Apply safe moves** only when `--apply` is passed. `--dry-run` is the default.

### Safety rules

- **Never delete** without explicit user action; archive instead.
- **Never guess** when metadata is insufficient; report recommendations.
- **Preserve confirmed preferences** during compaction; merge or summarize, do not erase.
- **Keep operations deterministic** so behavior is testable and reproducible.

### Namespace specificity & conflict resolution

When patterns contradict, apply these rules in order:

1. **More specific wins**: `project` > `domain` > `global`
   - A project-specific override takes precedence over a domain rule.
   - A domain rule takes precedence over a global preference.
2. **More recent wins** at the same specificity level
   - If two project rules conflict, the one with the later `Last-Seen` (or ID date) prevails.
3. **Ambiguous conflicts require asking the user**
   - If specificity is unclear or dates are identical, do not guess. Log a recommendation and ask.

### Compaction rules

When a file exceeds its tier limit:

1. **Merge** similar corrections or learnings into a single, summarized rule.
2. **Archive** unused patterns to COLD rather than deleting them.
3. **Summarize** verbose entries while preserving the verified "what works" fact.
4. **Never erase** confirmed preferences or hard-won corrections.

## Promotion rule of thumb

Promote a learning when it is:
- broadly applicable across multiple files or tasks
- likely to save future contributors time
- a stable convention rather than a one-off event
- better expressed as a short prevention rule than a full incident report

## Promotion targets

| Target | Best for |
|---|---|
| `CLAUDE.md` | Project facts, conventions, durable gotchas |
| `AGENTS.md` | Workflow rules, automation sequences, verification steps |
| `.github/copilot-instructions.md` | Shared Copilot context |
| `SOUL.md` | Behavioural rules in OpenClaw workspaces |
| `TOOLS.md` | Tool-specific gotchas in OpenClaw workspaces |

## Quantified promotion thresholds (legacy)

| Condition | Threshold | Action |
|---|---|---|
| HOT -> WARM | 30 days unused | Move to `domains/` or `projects/` |
| WARM -> COLD | 90 days unused | Move to `archive/` |
| WARM -> HOT | 3 uses within 7 days | Move to `memory.md` |
| To AGENTS/SOUL/TOOLS | `Recurrence-Count >= 3` + spans 2+ tasks + within 30 days | Promote as short prevention rule |
| To skill | Proven + broadly applicable | Extract as skill |

## Extraction criteria

Extract a reusable skill when most of these are true:
- the solution is resolved and tested
- the pattern is not tied to a single file or repo
- the fix is non-obvious enough to deserve specialised guidance
- the pattern has recurred or is likely to recur
- the resulting skill can stand on its own without original chat context

## Memory hygiene (GenericAgent-inspired)

The following principles are adapted from the GenericAgent memory-management model (MIT licensed). They help keep durable memory clean, accurate, and pointer-like.

### 1. Action-verified memory only
Only log a lesson as fact when it is based on an executed and verified observation (e.g. a command that ran, a file that was read, a test that passed). Do not store unverified assumptions, speculative fixes, or "I think" statements as durable memory.

> **Rule of thumb**: *No execution, no memory.* If you have not verified it, do not log it as fact.

### 2. No volatile state in durable memory
Avoid storing ephemeral or session-specific values that change frequently or become stale immediately. Examples to omit:
- Timestamps, session IDs, process PIDs
- Absolute temporary paths (`/tmp/...` on a specific machine)
- Connection handles, one-time tokens, or runtime device info
- "Current" versions or counts that will be wrong on the next run

Volatile context belongs in working memory or session notes, not in `learning/self-improving/`.

### 3. Index entries are pointers, not duplicates
The `index.md` Pattern-Key list and any cross-references should act as minimal pointers. They should tell a future reader *that* a pattern exists and *where* to find it, without duplicating the full details. If the index grows into a copy of the entries, it is too verbose.

### 4. Preserve verified facts during cleanup
When promoting, archiving, or refactoring entries, verified facts and fixes must survive intact. It is fine to compress wording or move an entry to a different tier, but do not drop the accurate "what was wrong" and "what works" information.

## Before extracting

Check:
- Does the new skill solve a real category of task?
- Can its description say exactly when it should trigger?
- Can you move detailed docs to `references/`?
- Can repeated logic be bundled into `scripts/`?
- Can you add at least a small eval set?
