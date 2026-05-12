#!/usr/bin/env python3
"""
learnings.py - Self-Improving Learning Log (Hybrid)

Merges actual-self-improvement execution core with self-improving-compound
HOT/WARM/COLD memory tiers.

Commands:
  init            Initialize learning/self-improving/ structure
  status          Show HOT/WARM/COLD tier statistics
  search          Search across all learning records
  log             Backward-compatible generic log (COR/LRN/FTR/ERR)
  log-correction  Log a correction to corrections.md
  log-learning    Log a learning to memory.md
  log-error       Log an error to memory.md
  log-feature     Log a feature request to memory.md
  maintain        Review and maintain memory lifecycle

Global options:
  --root PATH     Workspace root (default: OPENCLAW_WORKSPACE env, else cwd)
"""

from __future__ import annotations

import argparse
import difflib
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


def get_now() -> datetime:
    source_date = os.environ.get("SOURCE_DATE_EPOCH")
    if source_date:
        return datetime.fromtimestamp(int(source_date), tz=timezone.utc).astimezone()
    return datetime.now().astimezone()


def resolve_root(args: argparse.Namespace) -> Optional[str]:
    return getattr(args, "local_root", None) or args.root

SUBDIR_NAME = "learning/self-improving"

ID_PREFIXES = {
    "COR": "COR",
    "LRN": "LRN",
    "ERR": "ERR",
    "FTR": "FTR",
}

SECRET_PATTERNS = [
    re.compile(r'(?i)(api[_-]?key\s*[:=]\s*)["\']?[\w\-]{16,}["\']?', re.IGNORECASE),
    re.compile(r'(?i)(auth[_-]?token\s*[:=]\s*)["\']?[\w\-]{8,}["\']?', re.IGNORECASE),
    re.compile(r'(?i)(access[_-]?token\s*[:=]\s*)["\']?[\w\-]{8,}["\']?', re.IGNORECASE),
    re.compile(r'(?i)(password\s*[:=]\s*)["\']?[^\s"\']{4,}["\']?', re.IGNORECASE),
    re.compile(r'(?i)(secret\s*[:=]\s*)["\']?[\w\-]{8,}["\']?', re.IGNORECASE),
    re.compile(r'(?i)(client_secret\s*[:=]\s*)["\']?[\w\-]{8,}["\']?', re.IGNORECASE),
    re.compile(r'(?i)(authorization:\s*bearer\s+)[\w\-\.]+', re.IGNORECASE),
    re.compile(r'(?i)(authorization:\s*basic\s+)[\w\+/=]+', re.IGNORECASE),
    re.compile(r'(?i)(private[_-]?key\s*[:=]\s*)["\']?-----BEGIN[^\n]+', re.IGNORECASE),
    re.compile(r'(?i)(AKIA[0-9A-Z]{16})', re.IGNORECASE),
    re.compile(r'(?i)(sk-[a-zA-Z0-9]{20,})', re.IGNORECASE),
]

VOLATILE_PATTERNS = [
    re.compile(r'(?i)\b(pid|process\s+id)\s*[:=]?\s*\d+\b'),
    re.compile(r'(?i)\bsession[_-]?id\s*[:=]\s*[\w\-]{8,}\b'),
    re.compile(r'(?i)(?<![\w/])/tmp/[\w.-]+\b'),
    re.compile(r'(?i)\bcurrent\s+(timestamp|time|pid|session|dir|path)\b'),
    re.compile(r'\b\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?\b'),
]


def redact_secrets(text: str) -> str:
    for pattern in SECRET_PATTERNS:
        text = pattern.sub(r'\1[REDACTED]', text)
    return text


def check_volatile_patterns(text: str) -> List[str]:
    warnings: List[str] = []
    for pattern in VOLATILE_PATTERNS:
        for match in pattern.finditer(text):
            warnings.append(f"Volatile pattern detected: '{match.group(0)}'")
    return warnings


def get_base_dir(args_root: Optional[str]) -> Path:
    if args_root:
        root = Path(args_root).expanduser().resolve()
    else:
        env_root = os.environ.get("OPENCLAW_WORKSPACE")
        if env_root:
            root = Path(env_root).expanduser().resolve()
        else:
            root = Path.cwd().resolve()
    return root / SUBDIR_NAME


def ensure_structure(base_dir: Path) -> None:
    dirs = [
        base_dir,
        base_dir / "projects",
        base_dir / "domains",
        base_dir / "archive",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

    memory_file = base_dir / "memory.md"
    if not memory_file.exists():
        memory_file.write_text(
            "# Memory (HOT Tier)\n\n"
            "## ID Rules\n"
            "- All entries use format: `TYPE-YYYYMMDD-XXX` (e.g., COR-20230101-001)\n"
            "- Types: COR (correction), LRN (learning), FTR (feature), ERR (error)\n\n"
            "## Pattern-Key Rules\n"
            "- Recurring issues get a stable Pattern-Key (e.g., `markdown-table-telegram`)\n"
            "- Link related entries with `See Also: [Pattern-Key]`\n"
            "- Bump priority when Recurrence-Count >= 3 + spans 2+ tasks + within 30 days\n\n"
            "## Promotion Thresholds\n"
            "- HOT -> WARM: 30 days unused\n"
            "- WARM -> COLD: 90 days unused\n"
            "- WARM -> HOT: 3 uses within 7 days\n"
            "- To AGENTS.md/SOUL.md/TOOLS.md: proven + broadly applicable\n\n"
            "## Preferences\n"
            "<!-- Add your personal preferences here -->\n\n"
            "## Patterns\n"
            "<!-- Add recurring patterns here -->\n\n"
            "## Memory Hygiene\n"
            "- Action-verified only: log facts you have executed and verified, not assumptions.\n"
            "- No volatile state: avoid timestamps, session IDs, PIDs, temp paths, or 'current' values.\n"
            "- Pointers, not duplicates: index entries and cross-references should locate details, not repeat them.\n"
            "- Preserve facts on cleanup: compress or move entries, but keep the verified 'what works' intact.\n"
            "## Rules\n"
            "- Self-improving skill mode: Passive.\n"
            f"- Use `python3 scripts/learnings.py --root <workspace>` for logging/search/status.\n"
            "- Search before log to avoid duplicates.\n"
            "- Never log secrets, tokens, or private data.\n",
            encoding="utf-8",
        )

    corrections_file = base_dir / "corrections.md"
    if not corrections_file.exists():
        corrections_file.write_text(
            "# Corrections Log\n\n"
            "| ID | Date | Pattern-Key | What I Got Wrong | Correct Answer | Status |\n"
            "|------|------|-------------|------------------|----------------|--------|\n",
            encoding="utf-8",
        )

    index_file = base_dir / "index.md"
    if not index_file.exists():
        index_file.write_text(
            "# Memory Index\n\n"
            "| File | Lines | Last Updated |\n"
            "|------|-------|--------------|\n",
            encoding="utf-8",
        )


def count_lines(path: Path) -> int:
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return len(f.readlines())
    return 0


def generate_id(prefix: str, base_dir: Path) -> str:
    today = get_now().strftime("%Y%m%d")
    pattern = re.compile(rf"(?:^|\s){prefix}-{today}-(\d{{3}})\b")
    max_seq = 0
    search_files = [
        base_dir / "memory.md",
        base_dir / "corrections.md",
    ]
    for f in search_files:
        if f.exists():
            text = f.read_text(encoding="utf-8")
            for m in pattern.finditer(text):
                max_seq = max(max_seq, int(m.group(1)))
    for subdir in ["projects", "domains", "archive"]:
        for f in (base_dir / subdir).rglob("*.md"):
            if f.exists():
                text = f.read_text(encoding="utf-8")
                for m in pattern.finditer(text):
                    max_seq = max(max_seq, int(m.group(1)))
    seq = max_seq + 1
    return f"{prefix}-{today}-{seq:03d}"


def extract_pattern_keys(base_dir: Path) -> List[str]:
    keys: List[str] = []
    pattern = re.compile(r"Pattern-Key:\s*([^\]\n|]+)")
    for f in [base_dir / "memory.md", base_dir / "corrections.md"]:
        if f.exists():
            text = f.read_text(encoding="utf-8")
            keys.extend(k.strip() for k in pattern.findall(text) if k.strip())
    return keys


def update_index(base_dir: Path) -> None:
    today = get_now().strftime("%Y-%m-%d")
    lines = [
        "# Memory Index\n",
        "",
        "| File | Lines | Last Updated |",
        "|------|-------|--------------|",
    ]
    for f in ["memory.md", "corrections.md", "index.md"]:
        path = base_dir / f
        lines.append(f"| {f} | {count_lines(path)} | {today} |")

    warm_count = sum(
        1 for _ in (base_dir / "projects").rglob("*.md")
    ) + sum(1 for _ in (base_dir / "domains").rglob("*.md"))
    cold_count = sum(1 for _ in (base_dir / "archive").rglob("*.md"))

    lines.extend([
        "",
        "## Tiers",
        "",
        f"- HOT: memory.md, corrections.md",
        f"- WARM: {warm_count} files in projects/ + domains/",
        f"- COLD: {cold_count} files in archive/",
        "",
        "## Pattern-Key Index",
        "",
    ])

    pattern_keys = extract_pattern_keys(base_dir)
    if pattern_keys:
        for pk in sorted(set(pattern_keys)):
            lines.append(f"- `{pk}`")
    else:
        lines.append("_No Pattern-Keys indexed yet._")

    lines.append("")

    (base_dir / "index.md").write_text("\n".join(lines), encoding="utf-8")


def search_content(base_dir: Path, query: str, limit: int = 20) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    query_lower = query.lower()

    search_paths = [
        base_dir / "memory.md",
        base_dir / "corrections.md",
    ]
    for subdir in ["projects", "domains", "archive"]:
        search_paths.extend((base_dir / subdir).rglob("*.md"))

    for path in search_paths:
        if not path.exists():
            continue
        try:
            with open(path, "r", encoding="utf-8") as f:
                file_lines = f.readlines()
                for i, line in enumerate(file_lines, 1):
                    if query_lower in line.lower():
                        rel = path.relative_to(base_dir.parent) if path.is_relative_to(base_dir.parent) else path.name
                        results.append({
                            "file": str(rel),
                            "line": i,
                            "snippet": line.strip(),
                        })
                        if len(results) >= limit:
                            return results
        except Exception:
            continue
    return results


def cmd_init(args: argparse.Namespace) -> None:
    base_dir = get_base_dir(resolve_root(args))
    ensure_structure(base_dir)
    print(f"[init] Self-improving structure ready at: {base_dir}")
    print(f"[init] HOT  : memory.md, corrections.md")
    print(f"[init] WARM : projects/, domains/")
    print(f"[init] COLD : archive/")


def cmd_status(args: argparse.Namespace) -> None:
    base_dir = get_base_dir(resolve_root(args))
    ensure_structure(base_dir)

    hot_lines = count_lines(base_dir / "memory.md")
    corrections_lines = count_lines(base_dir / "corrections.md")
    warm_count = sum(
        1 for _ in (base_dir / "projects").rglob("*.md")
    ) + sum(1 for _ in (base_dir / "domains").rglob("*.md"))
    cold_count = sum(1 for _ in (base_dir / "archive").rglob("*.md"))

    seen_ids: set[str] = set()
    pattern_counts: Dict[str, int] = {}

    memory_text = (base_dir / "memory.md").read_text(encoding="utf-8") if (base_dir / "memory.md").exists() else ""
    for m in re.finditer(r"^### (\w+)-(\d{8}-\d{3})", memory_text, re.MULTILINE):
        prefix = m.group(1)
        entry_id = f"{prefix}-{m.group(2)}"
        if entry_id not in seen_ids:
            seen_ids.add(entry_id)
            pattern_counts[prefix] = pattern_counts.get(prefix, 0) + 1

    corrections_text = (base_dir / "corrections.md").read_text(encoding="utf-8") if (base_dir / "corrections.md").exists() else ""
    for m in re.finditer(r"\|\s*([A-Z]{3}-\d{8}-\d{3})\s*\|", corrections_text):
        entry_id = m.group(1)
        if entry_id not in seen_ids:
            seen_ids.add(entry_id)
            prefix = entry_id.split("-")[0]
            pattern_counts[prefix] = pattern_counts.get(prefix, 0) + 1

    pkeys = extract_pattern_keys(base_dir)

    fmt = getattr(args, "format", "text") or "text"

    if fmt == "json":
        import json
        out: Dict[str, Any] = {
            "hot": {
                "memory_lines": hot_lines,
                "corrections_lines": corrections_lines,
            },
            "warm": warm_count,
            "cold": cold_count,
            "entries_by_type": pattern_counts,
            "pattern_keys": len(set(pkeys)),
        }
        print(json.dumps(out, indent=2))
        return

    print("[status] Self-Improving Memory Status")
    print(f"  HOT   : memory.md ({hot_lines} lines), corrections.md ({corrections_lines} lines)")
    print(f"  WARM  : {warm_count} markdown files in projects/ + domains/")
    print(f"  COLD  : {cold_count} archived markdown files")

    if pattern_counts:
        print("  Entries by type:")
        for k, v in sorted(pattern_counts.items()):
            print(f"    {k}: {v}")

    if pkeys:
        print(f"  Pattern-Keys: {len(set(pkeys))} unique")


def cmd_search(args: argparse.Namespace) -> None:
    base_dir = get_base_dir(resolve_root(args))
    query = args.query or ""
    if not query:
        print("[search] Error: query required", file=sys.stderr)
        sys.exit(1)

    results = search_content(base_dir, query, limit=args.limit or 20)

    fmt = getattr(args, "format", "text") or "text"

    if fmt == "json":
        import json
        print(json.dumps(results, indent=2))
        return

    if not results:
        print(f"[search] No results for '{query}'")
        return

    print(f"[search] Found {len(results)} result(s) for '{query}':")
    for r in results:
        print(f"  {r['file']}:{r['line']} | {r['snippet'][:100]}")

    # Touch matched entries across all tiers — update Last-Seen and increment Recurrence-Count
    today = get_now().strftime("%Y-%m-%d")
    query_lower = query.lower()
    total_updated = 0

    touch_files: List[Path] = [base_dir / "memory.md"]
    for subdir in ["projects", "domains", "archive"]:
        touch_files.extend((base_dir / subdir).rglob("*.md"))

    for touch_file in touch_files:
        if not touch_file.exists():
            continue
        try:
            text = touch_file.read_text(encoding="utf-8")
            entries = _parse_entries(text)
            updated = 0
            for entry in entries:
                if query_lower in entry.get("full_text", "").lower():
                    old_text = entry["full_text"]
                    body = entry["body"]
                    meta = entry.get("metadata", {})
                    rc = int(meta.get("Recurrence-Count", "0"))
                    new_body = body
                    new_body = re.sub(
                        r"- \*\*Last-Seen\*\*:.*",
                        f"- **Last-Seen**: {today}",
                        new_body
                    )
                    new_body = re.sub(
                        r"- \*\*Recurrence-Count\*\*: \d+",
                        f"- **Recurrence-Count**: {rc + 1}",
                        new_body
                    )
                    new_full = old_text.replace(body, new_body)
                    text = text.replace(old_text, new_full)
                    updated += 1
            if updated > 0:
                touch_file.write_text(text, encoding="utf-8")
                total_updated += updated
        except Exception:
            pass

    if total_updated > 0:
        print(f"[search] Updated Recurrence-Count for {total_updated} entry/entries across all tiers")


def _append_to_memory(base_dir: Path, entry: str) -> None:
    target = base_dir / "memory.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    prefix = "\n" if target.exists() and target.read_text(encoding="utf-8").rstrip() else ""
    with target.open("a", encoding="utf-8") as f:
        f.write(prefix)
        f.write(entry.rstrip())
        f.write("\n")


def _append_to_corrections(base_dir: Path, row: str) -> None:
    target = base_dir / "corrections.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as f:
        f.write(row)


ENTRY_HEADING_RE = re.compile(r'^#{2,3}\s+.*[A-Z]{3}-\d{8}-\d{3}')


def parse_file_blocks(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    blocks: List[Dict[str, Any]] = []
    i = 0
    while i < len(lines):
        if ENTRY_HEADING_RE.match(lines[i]):
            start = i
            i += 1
            while i < len(lines):
                if ENTRY_HEADING_RE.match(lines[i]):
                    break
                i += 1
            block_lines = lines[start:i]
            while block_lines and block_lines[-1].strip() == "":
                block_lines.pop()
            block_text = "".join(block_lines)
            blocks.append({
                "text": block_text,
                "source": path,
            })
        else:
            i += 1
    return blocks


META_PATTERNS = [
    (re.compile(r'^[ \t]*[-*][ \t]+(?:\*\*)?Pattern-Key(?:\*\*)?[ \t]*[:：][ \t]*(.*?)$', re.IGNORECASE), "pattern_key"),
    (re.compile(r'^[ \t]*[-*][ \t]+(?:\*\*)?First-Seen(?:\*\*)?[ \t]*[:：][ \t]*(.*?)$', re.IGNORECASE), "first_seen"),
    (re.compile(r'^[ \t]*[-*][ \t]+(?:\*\*)?Last-Seen(?:\*\*)?[ \t]*[:：][ \t]*(.*?)$', re.IGNORECASE), "last_seen"),
    (re.compile(r'^[ \t]*[-*][ \t]+(?:\*\*)?Recurrence-Count(?:\*\*)?[ \t]*[:：][ \t]*(.*?)$', re.IGNORECASE), "recurrence_count"),
    (re.compile(r'^[ \t]*[-*][ \t]+(?:\*\*)?Area(?:\*\*)?[ \t]*[:：][ \t]*(.*?)$', re.IGNORECASE), "area"),
]


def parse_block_metadata(block_text: str) -> Dict[str, str]:
    meta: Dict[str, str] = {}
    for pattern, key in META_PATTERNS:
        for line in block_text.splitlines():
            m = pattern.match(line)
            if m:
                meta[key] = m.group(1).strip()
                break
    return meta


def extract_entry_id(block_text: str) -> Optional[str]:
    for line in block_text.splitlines():
        m = re.search(r'([A-Z]{3}-\d{8}-\d{3})', line)
        if m:
            return m.group(1)
    return None


def parse_date(date_str: str) -> Optional[datetime]:
    for fmt in ("%Y-%m-%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(date_str.strip(), fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def days_since(date_str: str) -> Optional[int]:
    dt = parse_date(date_str)
    if not dt:
        return None
    now = get_now().astimezone(timezone.utc)
    dt = dt.astimezone(timezone.utc)
    return (now - dt).days


def append_block_to_file(path: Path, block_text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        text = path.read_text(encoding="utf-8")
        text = text.rstrip()
        if text:
            text += "\n\n"
        text += block_text.rstrip() + "\n"
    else:
        text = block_text.rstrip() + "\n"
    path.write_text(text, encoding="utf-8")


def remove_block_from_file(path: Path, block_text: str) -> None:
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8")
    idx = text.find(block_text)
    if idx == -1:
        return
    before = text[:idx]
    after = text[idx + len(block_text):]
    before = before.rstrip()
    after = after.lstrip()
    new_text = before
    if after:
        new_text += "\n\n" + after
    new_text = new_text.rstrip() + "\n"
    path.write_text(new_text, encoding="utf-8")


def _do_dedup_check(base_dir: Path, content: str, force: bool) -> bool:
    existing = search_content(base_dir, content, limit=5)
    if not existing:
        return True
    exact = []
    similar = []
    for e in existing:
        snippet = e["snippet"]
        ratio = difflib.SequenceMatcher(None, content.lower(), snippet.lower()).ratio()
        if ratio > 0.8:
            exact.append(e)
        elif ratio > 0.6:
            similar.append(e)
    if exact:
        print(f"[log] Potential exact duplicates ({len(exact)}):")
        for e in exact:
            snippet = e["snippet"][:80]
            print(f"  - {e['file']}:{e['line']}: {snippet}...")
    if similar:
        print(f"[log] Similar entries found ({len(similar)}):")
        for e in similar:
            snippet = e["snippet"][:80]
            ratio = difflib.SequenceMatcher(None, content.lower(), snippet.lower()).ratio()
            print(f"  - {e['file']}:{e['line']} (similarity={ratio:.0%}): {snippet}...")
    if exact or similar:
        if not force:
            print("[log] Aborting. Use --force to skip dedup check.")
            return False
    return True


def _do_volatile_check(text: str, force: bool) -> bool:
    warnings = check_volatile_patterns(text)
    if warnings:
        print("[log] Warning: volatile state detected in entry:")
        for w in warnings[:3]:
            print(f"  - {w}")
        if len(warnings) > 3:
            print(f"  ... and {len(warnings) - 3} more")
        if not force:
            print("[log] Aborting. Use --force to log volatile content anyway.")
            return False
    return True


def cmd_log_correction(args: argparse.Namespace) -> None:
    base_dir = get_base_dir(resolve_root(args))
    ensure_structure(base_dir)

    summary = redact_secrets(args.summary or "")
    correct = redact_secrets(args.correct or "")
    pattern_key = args.pattern or ""

    if not summary:
        print("[log-correction] Error: --summary required", file=sys.stderr)
        sys.exit(1)

    search_term = f"{summary} {correct} {pattern_key}".strip()
    if not _do_dedup_check(base_dir, search_term, args.force):
        return
    if not _do_volatile_check(search_term, args.force):
        return

    entry_id = generate_id("COR", base_dir)
    today = get_now().strftime("%Y-%m-%d")

    row = f"| {entry_id} | {today} | {pattern_key} | {summary} | {correct} | ⏳ pending |\n"
    _append_to_corrections(base_dir, row)
    print(f"[log-correction] Logged: {entry_id}")

    update_index(base_dir)


def cmd_log_learning(args: argparse.Namespace) -> None:
    base_dir = get_base_dir(resolve_root(args))
    ensure_structure(base_dir)

    summary = redact_secrets(args.summary or "")
    details = redact_secrets(args.details or "")
    pattern_key = args.pattern or ""
    area = getattr(args, "area", "") or ""

    if not summary:
        print("[log-learning] Error: --summary required", file=sys.stderr)
        sys.exit(1)

    search_term = f"{summary} {details} {pattern_key}".strip()
    if not _do_dedup_check(base_dir, search_term, args.force):
        return
    if not _do_volatile_check(search_term, args.force):
        return

    entry_id = generate_id("LRN", base_dir)
    today = get_now().strftime("%Y-%m-%d")

    section = f"### {entry_id} ({today})"
    if pattern_key:
        section += f" [Pattern-Key: {pattern_key}]"
    section += f"\n- **Type**: LRN\n- **Summary**: {summary}\n"
    if details:
        section += f"- **Details**: {details}\n"
    if area:
        section += f"- **Area**: {area}\n"
    section += f"- **First-Seen**: {today}\n"
    section += f"- **Last-Seen**: {today}\n"
    section += f"- **Recurrence-Count**: 1\n"
    section += "\n"

    _append_to_memory(base_dir, section)
    print(f"[log-learning] Logged: {entry_id}")

    update_index(base_dir)


def cmd_log_error(args: argparse.Namespace) -> None:
    base_dir = get_base_dir(resolve_root(args))
    ensure_structure(base_dir)

    summary = redact_secrets(args.summary or "")
    details = redact_secrets(args.details or "")
    pattern_key = args.pattern or ""
    area = getattr(args, "area", "") or ""

    if not summary:
        print("[log-error] Error: --summary required", file=sys.stderr)
        sys.exit(1)

    search_term = f"{summary} {details} {pattern_key}".strip()
    if not _do_dedup_check(base_dir, search_term, args.force):
        return
    if not _do_volatile_check(search_term, args.force):
        return

    entry_id = generate_id("ERR", base_dir)
    today = get_now().strftime("%Y-%m-%d")

    section = f"### {entry_id} ({today})"
    if pattern_key:
        section += f" [Pattern-Key: {pattern_key}]"
    section += f"\n- **Type**: ERR\n- **Summary**: {summary}\n"
    if details:
        section += f"- **Details**: {details}\n"
    if area:
        section += f"- **Area**: {area}\n"
    section += f"- **First-Seen**: {today}\n"
    section += f"- **Last-Seen**: {today}\n"
    section += f"- **Recurrence-Count**: 1\n"
    section += "\n"

    _append_to_memory(base_dir, section)
    print(f"[log-error] Logged: {entry_id}")

    update_index(base_dir)


def cmd_log_feature(args: argparse.Namespace) -> None:
    base_dir = get_base_dir(resolve_root(args))
    ensure_structure(base_dir)

    summary = redact_secrets(args.summary or "")
    details = redact_secrets(args.details or "")
    pattern_key = args.pattern or ""
    area = getattr(args, "area", "") or ""

    if not summary:
        print("[log-feature] Error: --summary required", file=sys.stderr)
        sys.exit(1)

    search_term = f"{summary} {details} {pattern_key}".strip()
    if not _do_dedup_check(base_dir, search_term, args.force):
        return
    if not _do_volatile_check(search_term, args.force):
        return

    entry_id = generate_id("FTR", base_dir)
    today = get_now().strftime("%Y-%m-%d")

    section = f"### {entry_id} ({today})"
    if pattern_key:
        section += f" [Pattern-Key: {pattern_key}]"
    section += f"\n- **Type**: FTR\n- **Summary**: {summary}\n"
    if details:
        section += f"- **Details**: {details}\n"
    if area:
        section += f"- **Area**: {area}\n"
    section += f"- **First-Seen**: {today}\n"
    section += f"- **Last-Seen**: {today}\n"
    section += f"- **Recurrence-Count**: 1\n"
    section += "\n"

    _append_to_memory(base_dir, section)
    print(f"[log-feature] Logged: {entry_id}")

    update_index(base_dir)


def cmd_log(args: argparse.Namespace) -> None:
    base_dir = get_base_dir(resolve_root(args))
    ensure_structure(base_dir)

    log_type = (args.type or "LRN").upper()
    content = redact_secrets(args.content or "")
    pattern_key = args.pattern or ""
    correct = redact_secrets(args.correct or "")
    area = getattr(args, "area", "") or ""

    if not content:
        print("[log] Error: content required", file=sys.stderr)
        sys.exit(1)

    search_term = f"{content} {pattern_key}".strip()
    if not _do_dedup_check(base_dir, search_term, args.force):
        return
    if not _do_volatile_check(search_term, args.force):
        return

    today = get_now().strftime("%Y-%m-%d")

    if log_type == "COR":
        entry_id = generate_id("COR", base_dir)
        row = f"| {entry_id} | {today} | {pattern_key} | {content} | {correct} | ⏳ pending |\n"
        _append_to_corrections(base_dir, row)
        print(f"[log] Correction logged: {entry_id}")
    else:
        prefix = ID_PREFIXES.get(log_type, "LRN")
        entry_id = generate_id(prefix, base_dir)
        section = f"### {entry_id} ({today})"
        if pattern_key:
            section += f" [Pattern-Key: {pattern_key}]"
        section += f"\n- **Type**: {log_type}\n- **Summary**: {content}\n"
        if correct:
            section += f"- **Correct Answer**: {correct}\n"
        if area:
            section += f"- **Area**: {area}\n"
        section += f"- **First-Seen**: {today}\n"
        section += f"- **Last-Seen**: {today}\n"
        section += f"- **Recurrence-Count**: 1\n"
        section += "\n"
        _append_to_memory(base_dir, section)
        print(f"[log] Entry logged: {entry_id}")

    update_index(base_dir)


def _parse_date(date_str: str) -> Optional[datetime]:
    if not date_str:
        return None
    for fmt in ("%Y-%m-%d", "%Y%m%d"):
        try:
            return datetime.strptime(date_str.strip(), fmt).replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            continue
    return None


def _parse_entries(text: str) -> List[Dict[str, Any]]:
    entries: List[Dict[str, Any]] = []
    pattern = re.compile(
        r'^###\s+([A-Z]{3}-\d{8}-\d{3})\s+\(([^)]+)\)(?:\s*\[Pattern-Key:\s*([^\]]+)\])?\s*\n'
        r'(.*?)(?=^###\s+[A-Z]{3}-\d{8}-\d{3}|\Z)',
        re.MULTILINE | re.DOTALL,
    )
    for m in pattern.finditer(text):
        entry_id = m.group(1)
        date_str = m.group(2)
        pattern_key = (m.group(3) or "").strip()
        body = m.group(4)

        metadata: Dict[str, str] = {}
        for line in body.split("\n"):
            meta_match = re.match(r'- \*\*([^*]+)\*\*:\s*(.*)', line)
            if meta_match:
                key = meta_match.group(1).strip()
                value = meta_match.group(2).strip()
                metadata[key] = value

        first_seen = _parse_date(metadata.get("First-Seen", ""))
        last_seen = _parse_date(metadata.get("Last-Seen", ""))
        recurrence_count = 0
        try:
            recurrence_count = int(metadata.get("Recurrence-Count", "0"))
        except (ValueError, TypeError):
            pass

        entries.append({
            "id": entry_id,
            "date_str": date_str,
            "pattern_key": pattern_key,
            "body": body,
            "metadata": metadata,
            "first_seen": first_seen,
            "last_seen": last_seen,
            "recurrence_count": recurrence_count,
            "status": metadata.get("Status", ""),
            "area": metadata.get("Area", ""),
            "full_text": m.group(0),
            "start": m.start(),
            "end": m.end(),
        })
    return entries


def _remove_entries_from_text(text: str, entries_to_remove: List[Dict[str, Any]]) -> str:
    if not entries_to_remove:
        return text
    sorted_entries = sorted(entries_to_remove, key=lambda e: e["start"], reverse=True)
    result = text
    for entry in sorted_entries:
        result = result[:entry["start"]] + result[entry["end"]:]
    return result


def cmd_maintain(args: argparse.Namespace) -> None:
    base_dir = get_base_dir(resolve_root(args))
    ensure_structure(base_dir)

    now = get_now()
    apply_arg = getattr(args, "apply", None)
    if apply_arg is None:
        dry_run = getattr(args, "dry_run", True)
    else:
        dry_run = bool(getattr(args, "dry_run", False)) or not bool(apply_arg)
    fmt = getattr(args, "format", "text") or "text"

    results: Dict[str, List[Dict[str, Any]]] = {
        "stale_hot": [],
        "stale_warm": [],
        "promote_candidates": [],
        "promote_to_hot": [],
        "insufficient_metadata": [],
    }

    memory_file = base_dir / "memory.md"
    if memory_file.exists():
        text = memory_file.read_text(encoding="utf-8")
        entries = _parse_entries(text)
        for entry in entries:
            last_seen = entry.get("last_seen")
            if last_seen is None:
                last_seen = _parse_date(entry.get("date_str", ""))

            if last_seen is None:
                results["insufficient_metadata"].append({
                    "id": entry["id"],
                    "reason": "missing Last-Seen",
                    "source": "memory.md",
                })
                continue

            days_since = (now - last_seen).days
            if days_since >= 30:
                area = entry.get("area", "") or "general"
                if area.startswith("project:"):
                    target_rel = f"projects/{area[8:]}.md"
                elif area.startswith("domain:"):
                    target_rel = f"domains/{area[7:]}.md"
                else:
                    target_rel = "domains/general.md"

                results["stale_hot"].append({
                    "id": entry["id"],
                    "last_seen": last_seen.strftime("%Y-%m-%d"),
                    "days_stale": days_since,
                    "action": "HOT_TO_WARM",
                    "target": target_rel,
                    "source": "memory.md",
                    "entry": entry,
                })

            recurrence = entry.get("recurrence_count", 0)
            if recurrence >= 3:
                results["promote_candidates"].append({
                    "id": entry["id"],
                    "recurrence_count": recurrence,
                    "action": "PROMOTE_CANDIDATE",
                    "source": "memory.md",
                })

    warm_files: List[Path] = []
    for subdir in ["projects", "domains"]:
        warm_files.extend((base_dir / subdir).rglob("*.md"))

    for warm_file in warm_files:
        text = warm_file.read_text(encoding="utf-8")
        entries = _parse_entries(text)
        rel_path = str(warm_file.relative_to(base_dir))
        for entry in entries:
            last_seen = entry.get("last_seen")
            if last_seen is None:
                last_seen = _parse_date(entry.get("date_str", ""))

            if last_seen is None:
                results["insufficient_metadata"].append({
                    "id": entry["id"],
                    "reason": "missing Last-Seen",
                    "source": rel_path,
                })
                continue

            days_since = (now - last_seen).days
            if days_since >= 90:
                archive_name = warm_file.stem + ".md"
                target_rel = f"archive/{archive_name}"

                results["stale_warm"].append({
                    "id": entry["id"],
                    "last_seen": last_seen.strftime("%Y-%m-%d"),
                    "days_stale": days_since,
                    "action": "WARM_TO_COLD",
                    "target": target_rel,
                    "source": rel_path,
                    "entry": entry,
                })

            recurrence = entry.get("recurrence_count", 0)
            if recurrence >= 3:
                days_since_last = days_since(entry.get("metadata", {}).get("Last-Seen", ""))
                if last_seen and days_since_last is not None and days_since_last <= 7:
                    results["promote_to_hot"].append({
                        "id": entry["id"],
                        "last_seen": last_seen.strftime("%Y-%m-%d"),
                        "days_since": days_since_last,
                        "recurrence_count": recurrence,
                        "action": "WARM_TO_HOT",
                        "source": rel_path,
                        "entry": entry,
                    })
                results["promote_candidates"].append({
                    "id": entry["id"],
                    "recurrence_count": recurrence,
                    "action": "PROMOTE_CANDIDATE",
                    "source": rel_path,
                })

    if not dry_run:
        if results["stale_hot"]:
            memory_text = memory_file.read_text(encoding="utf-8") if memory_file.exists() else ""
            entries_to_remove = [r["entry"] for r in results["stale_hot"]]

            by_target: Dict[str, List[Dict[str, Any]]] = {}
            for r in results["stale_hot"]:
                by_target.setdefault(r["target"], []).append(r)

            for target_rel, items in by_target.items():
                target_path = base_dir / target_rel
                for item in items:
                    append_block_to_file(target_path, item["entry"]["full_text"])

            new_memory_text = _remove_entries_from_text(memory_text, entries_to_remove)
            if new_memory_text != memory_text:
                memory_file.write_text(new_memory_text, encoding="utf-8")

        if results["stale_warm"]:
            by_source: Dict[str, List[Dict[str, Any]]] = {}
            for r in results["stale_warm"]:
                by_source.setdefault(r["source"], []).append(r)

            for source_rel, items in by_source.items():
                source_path = base_dir / source_rel
                source_text = source_path.read_text(encoding="utf-8")
                entries_to_remove = [item["entry"] for item in items]

                by_target2: Dict[str, List[Dict[str, Any]]] = {}
                for item in items:
                    by_target2.setdefault(item["target"], []).append(item)

                for target_rel, target_items in by_target2.items():
                    target_path = base_dir / target_rel
                    for item in target_items:
                        append_block_to_file(target_path, item["entry"]["full_text"])

                new_source_text = _remove_entries_from_text(source_text, entries_to_remove)
                if new_source_text != source_text:
                    source_path.write_text(new_source_text, encoding="utf-8")

    # WARM→HOT: promote entries with Recurrence-Count >= 3 and Last-Seen within 7 days
    if not dry_run and results.get("promote_to_hot"):
        memory_text = memory_file.read_text(encoding="utf-8") if memory_file.exists() else ""
        for r in results["promote_to_hot"]:
            # Remove from WARM file
            source_path = base_dir / r["source"]
            if source_path.exists():
                source_text = source_path.read_text(encoding="utf-8")
                source_text = _remove_entries_from_text(source_text, [r["entry"]])
                source_path.write_text(source_text, encoding="utf-8")
            # Append to HOT memory.md
            append_block_to_file(memory_file, r["entry"]["full_text"])

    if fmt == "json":
        json_out = {
            "stale_hot": [{k: v for k, v in r.items() if k != "entry"} for r in results["stale_hot"]],
            "stale_warm": [{k: v for k, v in r.items() if k != "entry"} for r in results["stale_warm"]],
            "promote_candidates": results["promote_candidates"],
            "insufficient_metadata": results["insufficient_metadata"],
        }
        import json
        print(json.dumps(json_out, indent=2))
    else:
        print("[maintain] Scanning memory tiers...")
        has_any = bool(results["stale_hot"] or results["stale_warm"] or results["promote_candidates"] or results["insufficient_metadata"])
        if results["stale_hot"]:
            print("HOT -> WARM (stale >= 30 days):")
            for r in results["stale_hot"]:
                print(f"  - {r['id']}: Last-Seen {r['last_seen']} ({r['days_stale']} days ago) -> {r['target']}")
        if results["stale_warm"]:
            print("WARM -> COLD (stale >= 90 days):")
            for r in results["stale_warm"]:
                print(f"  - {r['id']} in {r['source']}: Last-Seen {r['last_seen']} ({r['days_stale']} days ago) -> {r['target']}")
        if results["promote_candidates"]:
            print("Promotion candidates:")
            for r in results["promote_candidates"]:
                print(f"  - {r['id']}: Recurrence-Count={r['recurrence_count']}")
        if results["insufficient_metadata"]:
            print("Insufficient metadata:")
            for r in results["insufficient_metadata"]:
                print(f"  - {r['id']}: {r['reason']}")
        if not has_any:
            print("  All entries healthy. No action needed.")



def cmd_promote(args: argparse.Namespace) -> None:
    """Promote an entry from its current tier to a target memory file."""
    base_dir = get_base_dir(resolve_root(args))
    ensure_structure(base_dir)
    entry_id = args.entry_id
    target_file = args.to or ""
    if not target_file:
        print("[promote] Error: --to TARGET is required", file=sys.stderr)
        sys.exit(1)
    found_entry = None
    found_source = None
    for src in [base_dir / "memory.md"] + list((base_dir / "projects").rglob("*.md")) + list((base_dir / "domains").rglob("*.md")):
        if not src.exists():
            continue
        text = src.read_text(encoding="utf-8")
        entries = _parse_entries(text)
        for e in entries:
            if e["id"] == entry_id:
                found_entry = e
                found_source = src
                break
        if found_entry:
            break
    if not found_entry:
        print(f"[promote] Entry {entry_id} not found", file=sys.stderr)
        sys.exit(1)
    target_path = base_dir.parent / target_file if "/" in target_file or not target_file.endswith(".md") else base_dir.parent / target_file
    if not target_path.parent.exists():
        target_path.parent.mkdir(parents=True, exist_ok=True)
    promoted_text = found_entry["full_text"] + f"\n- **Status**: promoted\n- **Promoted-To**: {target_file}\n"
    append_block_to_file(target_path, promoted_text)
    src_text = found_source.read_text(encoding="utf-8")
    src_text = _remove_entries_from_text(src_text, [found_entry])
    found_source.write_text(src_text, encoding="utf-8")
    print(f"[promote] Moved {entry_id} from {found_source.relative_to(base_dir.parent)} to {target_file}")
    update_index(base_dir)


def cmd_edit(args: argparse.Namespace) -> None:
    """Edit metadata of an existing entry in-place."""
    base_dir = get_base_dir(resolve_root(args))
    ensure_structure(base_dir)
    entry_id = args.entry_id
    new_status = getattr(args, "status", None)
    new_last_seen = getattr(args, "last_seen", None)
    new_recurrence = getattr(args, "recurrence", None)

    if not any([new_status, new_last_seen, new_recurrence]):
        print("[edit] Error: at least one of --status, --last-seen, --recurrence is required", file=sys.stderr)
        sys.exit(1)

    found = False
    for src in [base_dir / "memory.md"] + list((base_dir / "projects").rglob("*.md")) + list((base_dir / "domains").rglob("*.md")) + list((base_dir / "archive").rglob("*.md")):
        if not src.exists():
            continue
        text = src.read_text(encoding="utf-8")
        entries = _parse_entries(text)
        for e in entries:
            if e["id"] == entry_id:
                old_text = e["full_text"]
                new_text = old_text
                if new_status:
                    new_text = re.sub(r"- \*\*Status\*\*:.*", f"- **Status**: {new_status}", new_text)
                    if "- **Status**:" not in new_text:
                        new_text = new_text.rstrip() + f"\n- **Status**: {new_status}\n"
                if new_last_seen:
                    new_text = re.sub(r"- \*\*Last-Seen\*\*:.*", f"- **Last-Seen**: {new_last_seen}", new_text)
                if new_recurrence is not None:
                    new_text = re.sub(r"- \*\*Recurrence-Count\*\*: \\d+", f"- **Recurrence-Count**: {new_recurrence}", new_text)
                text = text.replace(old_text, new_text)
                src.write_text(text, encoding="utf-8")
                print(f"[edit] Updated {entry_id}")
                found = True
                break
        if found:
            break
    if not found:
        print(f"[edit] Entry {entry_id} not found", file=sys.stderr)
        sys.exit(1)

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Self-Improving Learning Log (Hybrid)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Environment:
  OPENCLAW_WORKSPACE    Default workspace root if --root is not provided.

Examples:
  %(prog)s --root /path/to/workspace init
  %(prog)s --root /path/to/workspace log-correction --summary "Used wrong format" --correct "Use lists" --pattern telegram-format --force
  %(prog)s --root /path/to/workspace log-learning --summary "Search before logging" --details "Avoid duplicates" --pattern dedupe-rule --force
  %(prog)s --root /path/to/workspace search telegram
  %(prog)s --root /path/to/workspace status
  %(prog)s status --root /path/to/workspace --format json
  %(prog)s --root /path/to/workspace maintain
  %(prog)s --root /path/to/workspace maintain --apply
        """,
    )
    parser.add_argument(
        "--root",
        default=None,
        help="Workspace root (default: OPENCLAW_WORKSPACE env, else current directory)",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    def _add_root(parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--root",
            dest="local_root",
            default=None,
            help="Workspace root (overrides global --root)",
        )

    p_init = sub.add_parser("init", help="Initialize learning/self-improving/ structure")
    _add_root(p_init)
    p_init.set_defaults(func=cmd_init)

    p_status = sub.add_parser("status", help="Show memory status")
    _add_root(p_status)
    p_status.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    p_status.set_defaults(func=cmd_status)

    p_search = sub.add_parser("search", help="Search learning records")
    _add_root(p_search)
    p_search.add_argument("query", nargs="?", help="Search query")
    p_search.add_argument("--limit", "-l", type=int, default=20, help="Result limit")
    p_search.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    p_search.set_defaults(func=cmd_search)

    p_log = sub.add_parser("log", help="Log a learning (backward-compatible)")
    _add_root(p_log)
    p_log.add_argument("content", nargs="?", help="Learning content")
    p_log.add_argument("--type", "-t", default="LRN", help="Entry type (COR/LRN/FTR/ERR)")
    p_log.add_argument("--pattern", "-p", default="", help="Pattern-Key identifier")
    p_log.add_argument("--correct", "-c", default="", help="Correct answer (for COR type)")
    p_log.add_argument("--area", "-a", default="", help="Area (project:name or domain:name)")
    p_log.add_argument("--force", "-f", action="store_true", help="Skip dedup check")
    p_log.set_defaults(func=cmd_log)

    p_logc = sub.add_parser("log-correction", help="Log a correction")
    _add_root(p_logc)
    p_logc.add_argument("--summary", "-s", required=True, help="What went wrong")
    p_logc.add_argument("--correct", "-c", required=True, help="The correct answer")
    p_logc.add_argument("--pattern", "-p", default="", help="Pattern-Key identifier")
    p_logc.add_argument("--area", "-a", default="", help="Area (project:name or domain:name)")
    p_logc.add_argument("--force", "-f", action="store_true", help="Skip dedup check")
    p_logc.set_defaults(func=cmd_log_correction)

    p_logl = sub.add_parser("log-learning", help="Log a learning")
    _add_root(p_logl)
    p_logl.add_argument("--summary", "-s", required=True, help="Learning summary")
    p_logl.add_argument("--details", "-d", default="", help="Learning details")
    p_logl.add_argument("--pattern", "-p", default="", help="Pattern-Key identifier")
    p_logl.add_argument("--area", "-a", default="", help="Area (project:name or domain:name)")
    p_logl.add_argument("--force", "-f", action="store_true", help="Skip dedup check")
    p_logl.set_defaults(func=cmd_log_learning)

    p_loge = sub.add_parser("log-error", help="Log an error")
    _add_root(p_loge)
    p_loge.add_argument("--summary", "-s", required=True, help="Error summary")
    p_loge.add_argument("--details", "-d", default="", help="Error details")
    p_loge.add_argument("--pattern", "-p", default="", help="Pattern-Key identifier")
    p_loge.add_argument("--area", "-a", default="", help="Area (project:name or domain:name)")
    p_loge.add_argument("--force", "-f", action="store_true", help="Skip dedup check")
    p_loge.set_defaults(func=cmd_log_error)

    p_logf = sub.add_parser("log-feature", help="Log a feature request")
    _add_root(p_logf)
    p_logf.add_argument("--summary", "-s", required=True, help="Feature summary")
    p_logf.add_argument("--details", "-d", default="", help="Feature details")
    p_logf.add_argument("--pattern", "-p", default="", help="Pattern-Key identifier")
    p_logf.add_argument("--area", "-a", default="", help="Area (project:name or domain:name)")
    p_logf.add_argument("--force", "-f", action="store_true", help="Skip dedup check")
    p_logf.set_defaults(func=cmd_log_feature)

    p_maintain = sub.add_parser("maintain", help="Maintain memory lifecycle")
    _add_root(p_maintain)
    p_maintain.add_argument("--apply", dest="dry_run", action="store_false", help="Apply moves (default is dry-run)")
    p_maintain.add_argument("--dry-run", dest="dry_run", action="store_true", default=True, help="Show what would be done without applying")
    p_maintain.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    p_maintain.set_defaults(func=cmd_maintain)

    p_promote = sub.add_parser("promote", help="Promote an entry to a target memory file")
    _add_root(p_promote)
    p_promote.add_argument("entry_id", help="Entry ID (e.g., LRN-20260512-001)")
    p_promote.add_argument("--to", "-t", required=True, help="Target file path (e.g., CLAUDE.md or projects/foo.md)")
    p_promote.set_defaults(func=cmd_promote)

    p_edit = sub.add_parser("edit", help="Edit entry metadata in-place")
    _add_root(p_edit)
    p_edit.add_argument("entry_id", help="Entry ID (e.g., COR-20260512-001)")
    p_edit.add_argument("--status", choices=["pending", "in_progress", "resolved", "wont_fix", "promoted", "promoted_to_skill"], help="New status")
    p_edit.add_argument("--last-seen", help="New Last-Seen date (YYYY-MM-DD)")
    p_edit.add_argument("--recurrence", type=int, help="New Recurrence-Count")
    p_edit.set_defaults(func=cmd_edit)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        args.func(args)
        return 0
    except SystemExit as e:
        return e.code if isinstance(e.code, int) else 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
