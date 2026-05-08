#!/usr/bin/env python3
"""
learnings.py - Self-Improving Learning Log
Adapted for OpenClaw stock v1.2.16 structure
Commands: init, log, search, status
"""

import os
import sys
import re
import argparse
from datetime import datetime
from pathlib import Path

BASE_DIR = Path.home() / "self-improving"
MEMORY_FILE = BASE_DIR / "memory.md"
CORRECTIONS_FILE = BASE_DIR / "corrections.md"
INDEX_FILE = BASE_DIR / "index.md"
PROJECTS_DIR = BASE_DIR / "projects"
DOMAINS_DIR = BASE_DIR / "domains"
ARCHIVE_DIR = BASE_DIR / "archive"

ID_PATTERNS = {
    "COR": "COR-YYYYMMDD-XXX",   # Correction
    "LRN": "LRN-YYYYMMDD-XXX",   # Learning
    "FTR": "FTR-YYYYMMDD-XXX",   # Feature
    "ERR": "ERR-YYYYMMDD-XXX",   # Error
}

def generate_id(prefix: str) -> str:
    """Generate ID like COR-20260508-001"""
    today = datetime.now().strftime("%Y%m%d")
    # Find existing IDs with same prefix and date
    pattern = re.compile(rf"^{prefix}-{today}-(\d{{3}})")
    max_seq = 0
    for file in [MEMORY_FILE, CORRECTIONS_FILE]:
        if file.exists():
            with open(file, "r", encoding="utf-8") as f:
                for line in f:
                    m = pattern.search(line)
                    if m:
                        max_seq = max(max_seq, int(m.group(1)))
    seq = max_seq + 1
    return f"{prefix}-{today}-{seq:03d}"

def ensure_structure():
    """Ensure all required directories and files exist."""
    for d in [BASE_DIR, PROJECTS_DIR, DOMAINS_DIR, ARCHIVE_DIR]:
        d.mkdir(parents=True, exist_ok=True)
    for f, template in [
        (MEMORY_FILE, "# Memory (HOT Tier)\n\n## Preferences\n\n## Patterns\n\n## Rules\n"),
        (CORRECTIONS_FILE, "# Corrections Log\n\n| ID | Date | Pattern-Key | What I Got Wrong | Correct Answer | Status |\n|------|------|-------------|------------------|----------------|--------|\n"),
        (INDEX_FILE, "# Memory Index\n\n| File | Lines | Last Updated |\n|------|-------|--------------|\n"),
    ]:
        if not f.exists():
            f.write_text(template, encoding="utf-8")
            print(f"[init] Created {f.name}")

def cmd_init(args):
    """Initialize or verify the self-improving directory structure."""
    ensure_structure()
    print("[init] Self-improving structure ready.")
    print(f"[init] Base: {BASE_DIR}")

def cmd_log(args):
    """Log a learning, correction, feature, or error."""
    ensure_structure()
    log_type = (args.type or "LRN").upper()
    content = args.content or ""
    pattern_key = args.pattern or ""
    
    if not content:
        print("[log] Error: content required")
        sys.exit(1)
    
    # search-before-log deduplication
    existing = search_content(content, limit=3)
    if existing:
        print(f"[log] Potential duplicates found ({len(existing)}):")
        for e in existing:
            print(f"  - {e['file']}:{e['line']}: {e['snippet'][:80]}...")
        if not args.force:
            confirm = input("[log] Proceed anyway? [y/N]: ")
            if confirm.lower() != "y":
                print("[log] Aborted.")
                return
    
    entry_id = generate_id(log_type)
    today = datetime.now().strftime("%Y-%m-%d")
    
    if log_type == "COR":
        # Append to corrections.md as table row
        row = f"| {entry_id} | {today} | {pattern_key} | {content} | {args.correct or ''} | ⏳ pending |\n"
        with open(CORRECTIONS_FILE, "a", encoding="utf-8") as f:
            f.write(row)
        print(f"[log] Correction logged: {entry_id}")
    else:
        # Append to memory.md
        section = f"\n### {entry_id} ({today})"
        if pattern_key:
            section += f" [Pattern-Key: {pattern_key}]"
        section += f"\n- **Type**: {log_type}\n- **Content**: {content}\n"
        with open(MEMORY_FILE, "a", encoding="utf-8") as f:
            f.write(section)
        print(f"[log] Learning logged: {entry_id}")
    
    update_index()

def search_content(query: str, limit: int = 10) -> list:
    """Search memory.md, corrections.md, projects/, domains/."""
    results = []
    query_lower = query.lower()
    
    # Search files
    search_paths = [
        MEMORY_FILE,
        CORRECTIONS_FILE,
        *list(PROJECTS_DIR.rglob("*.md")),
        *list(DOMAINS_DIR.rglob("*.md")),
    ]
    
    for path in search_paths:
        if not path.exists():
            continue
        try:
            with open(path, "r", encoding="utf-8") as f:
                lines = f.readlines()
                for i, line in enumerate(lines, 1):
                    if query_lower in line.lower():
                        results.append({
                            "file": path.relative_to(BASE_DIR),
                            "line": i,
                            "snippet": line.strip(),
                        })
                        if len(results) >= limit:
                            return results
        except Exception as e:
            continue
    return results

def cmd_search(args):
    """Search across all learning records."""
    query = args.query or ""
    if not query:
        print("[search] Error: query required")
        sys.exit(1)
    
    results = search_content(query, limit=args.limit or 20)
    if not results:
        print(f"[search] No results for '{query}'")
        return
    
    print(f"[search] Found {len(results)} result(s) for '{query}':")
    for r in results:
        print(f"  {r['file']}:{r['line']} | {r['snippet'][:100]}")

def count_lines(path: Path) -> int:
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return len(f.readlines())
    return 0

def update_index():
    """Update index.md with current line counts and timestamps."""
    today = datetime.now().strftime("%Y-%m-%d")
    lines = [
        "# Memory Index\n",
        "| File | Lines | Last Updated |",
        "|------|-------|--------------|",
    ]
    for f in [MEMORY_FILE, CORRECTIONS_FILE, BASE_DIR / "heartbeat-state.md"]:
        lines.append(f"| {f.name} | {count_lines(f)} | {today} |")
    
    # Add Pattern-Key index section
    lines.extend([
        "",
        "## Pattern-Key Index",
        "",
    ])
    pattern_keys = extract_pattern_keys()
    if pattern_keys:
        for pk in sorted(set(pattern_keys)):
            lines.append(f"- `{pk}`")
    else:
        lines.append("_No Pattern-Keys indexed yet._")
    
    INDEX_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")

def extract_pattern_keys() -> list:
    """Extract all Pattern-Keys from memory.md and corrections.md."""
    keys = []
    pattern = re.compile(r"Pattern-Key:\s*([^\]\n]+)")
    for f in [MEMORY_FILE, CORRECTIONS_FILE]:
        if f.exists():
            text = f.read_text(encoding="utf-8")
            keys.extend(pattern.findall(text))
    return keys

def cmd_status(args):
    """Show HOT/WARM/COLD tier statistics."""
    ensure_structure()
    
    hot_lines = count_lines(MEMORY_FILE)
    corrections_lines = count_lines(CORRECTIONS_FILE)
    warm_count = len(list(PROJECTS_DIR.rglob("*.md"))) + len(list(DOMAINS_DIR.rglob("*.md")))
    cold_count = len(list(ARCHIVE_DIR.rglob("*.md")))
    
    print("[status] Self-Improving Memory Status")
    print(f"  HOT   : memory.md ({hot_lines} lines), corrections.md ({corrections_lines} lines)")
    print(f"  WARM  : {warm_count} markdown files in projects/ + domains/")
    print(f"  COLD  : {cold_count} archived markdown files")
    
    # Count entries by type
    pattern_counts = {}
    text = MEMORY_FILE.read_text(encoding="utf-8") if MEMORY_FILE.exists() else ""
    for m in re.finditer(r"^### (\w+)-", text, re.MULTILINE):
        prefix = m.group(1)
        pattern_counts[prefix] = pattern_counts.get(prefix, 0) + 1
    
    if pattern_counts:
        print("  Entries by type:")
        for k, v in sorted(pattern_counts.items()):
            print(f"    {k}: {v}")
    
    # Pattern-Key summary
    pkeys = extract_pattern_keys()
    if pkeys:
        print(f"  Pattern-Keys: {len(set(pkeys))} unique")

def main():
    parser = argparse.ArgumentParser(description="Self-Improving Learning Log")
    sub = parser.add_subparsers(dest="command")
    
    p_init = sub.add_parser("init", help="Initialize structure")
    
    p_log = sub.add_parser("log", help="Log a learning")
    p_log.add_argument("content", nargs="?", help="Learning content")
    p_log.add_argument("--type", "-t", default="LRN", help="Entry type (COR/LRN/FTR/ERR)")
    p_log.add_argument("--pattern", "-p", default="", help="Pattern-Key identifier")
    p_log.add_argument("--correct", "-c", default="", help="Correct answer (for COR type)")
    p_log.add_argument("--force", "-f", action="store_true", help="Skip dedup check")
    
    p_search = sub.add_parser("search", help="Search learning records")
    p_search.add_argument("query", nargs="?", help="Search query")
    p_search.add_argument("--limit", "-l", type=int, default=20, help="Result limit")
    
    p_status = sub.add_parser("status", help="Show memory status")
    
    args = parser.parse_args()
    
    if args.command == "init":
        cmd_init(args)
    elif args.command == "log":
        cmd_log(args)
    elif args.command == "search":
        cmd_search(args)
    elif args.command == "status":
        cmd_status(args)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
