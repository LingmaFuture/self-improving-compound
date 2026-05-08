#!/usr/bin/env python3

import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import learnings as L


class TestGetNow:
    def test_returns_local_time_by_default(self):
        now = L.get_now()
        assert now.tzinfo is not None
        assert now.strftime("%Y%m%d") == datetime.now().astimezone().strftime("%Y%m%d")

    def test_respects_source_date_epoch(self):
        epoch = "1700000000"
        old = os.environ.pop("SOURCE_DATE_EPOCH", None)
        try:
            os.environ["SOURCE_DATE_EPOCH"] = epoch
            now = L.get_now()
            expected = datetime.fromtimestamp(int(epoch), tz=timezone.utc).astimezone()
            assert now.year == expected.year
            assert now.month == expected.month
            assert now.day == expected.day
        finally:
            if old is not None:
                os.environ["SOURCE_DATE_EPOCH"] = old
            else:
                os.environ.pop("SOURCE_DATE_EPOCH", None)


class TestRedactSecrets:
    def test_api_key_redaction(self):
        text = 'api_key = "sk-12345678901234567890"'
        result = L.redact_secrets(text)
        assert "[REDACTED]" in result
        assert "sk-12345678901234567890" not in result

    def test_bearer_token_redaction(self):
        text = "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
        result = L.redact_secrets(text)
        assert "[REDACTED]" in result

    def test_no_false_positives_on_short_strings(self):
        text = "password = ok"
        result = L.redact_secrets(text)
        assert "[REDACTED]" not in result


class TestResolveRoot:
    def test_prefers_local_root(self):
        class Args:
            root = "/global"
            local_root = "/local"
        assert L.resolve_root(Args()) == "/local"

    def test_falls_back_to_global_root(self):
        class Args:
            root = "/global"
            local_root = None
        assert L.resolve_root(Args()) == "/global"

    def test_falls_back_to_root_when_local_missing_attr(self):
        class Args:
            root = "/global"
        assert L.resolve_root(Args()) == "/global"


class TestStatusCounts:
    def test_counts_memory_headings_and_correction_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / ".learnings" / "self-improving"
            base.mkdir(parents=True)

            memory = base / "memory.md"
            memory.write_text(
                "# Memory\n\n"
                "### LRN-20260509-001 (2026-05-09)\n- **Type**: LRN\n"
                "### ERR-20260509-002 (2026-05-09)\n- **Type**: ERR\n",
                encoding="utf-8",
            )

            corrections = base / "corrections.md"
            corrections.write_text(
                "# Corrections\n\n"
                "| ID | Date | Pattern-Key | What I Got Wrong | Correct Answer | Status |\n"
                "|------|------|-------------|------------------|----------------|--------|\n"
                "| COR-20260509-003 | 2026-05-09 | pk | wrong | right | pending |\n",
                encoding="utf-8",
            )

            class Args:
                root = tmp
                local_root = None
                format = "json"

            import io
            from contextlib import redirect_stdout

            f = io.StringIO()
            with redirect_stdout(f):
                L.cmd_status(Args())

            import json
            data = json.loads(f.getvalue())
            assert data["entries_by_type"]["LRN"] == 1
            assert data["entries_by_type"]["ERR"] == 1
            assert data["entries_by_type"]["COR"] == 1

    def test_avoids_double_counting_duplicate_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / ".learnings" / "self-improving"
            base.mkdir(parents=True)

            memory = base / "memory.md"
            memory.write_text(
                "# Memory\n\n"
                "### COR-20260509-001 (2026-05-09)\n- **Type**: COR\n",
                encoding="utf-8",
            )

            corrections = base / "corrections.md"
            corrections.write_text(
                "# Corrections\n\n"
                "| ID | Date | Pattern-Key | What I Got Wrong | Correct Answer | Status |\n"
                "|------|------|-------------|------------------|----------------|--------|\n"
                "| COR-20260509-001 | 2026-05-09 | pk | wrong | right | pending |\n",
                encoding="utf-8",
            )

            class Args:
                root = tmp
                local_root = None
                format = "json"

            import io
            from contextlib import redirect_stdout

            f = io.StringIO()
            with redirect_stdout(f):
                L.cmd_status(Args())

            import json
            data = json.loads(f.getvalue())
            assert data["entries_by_type"]["COR"] == 1


class TestCliRootCompatibility:
    def test_global_root_before_subcommand(self):
        parser = L.build_parser()
        args = parser.parse_args(["--root", "/tmp/foo", "status"])
        assert args.root == "/tmp/foo"
        assert getattr(args, "local_root", None) is None

    def test_local_root_after_subcommand(self):
        parser = L.build_parser()
        args = parser.parse_args(["status", "--root", "/tmp/bar"])
        assert args.root is None
        assert args.local_root == "/tmp/bar"


class TestGenerateId:
    def test_id_uses_local_date(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / ".learnings" / "self-improving"
            base.mkdir(parents=True)
            today = datetime.now().astimezone().strftime("%Y%m%d")
            entry_id = L.generate_id("LRN", base)
            assert entry_id.startswith(f"LRN-{today}-")


class TestSearchJsonFormat:
    def test_json_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / ".learnings" / "self-improving"
            base.mkdir(parents=True)

            memory = base / "memory.md"
            memory.write_text("# Memory\n\nhello world\n", encoding="utf-8")

            class Args:
                root = tmp
                local_root = None
                query = "hello"
                limit = 20
                format = "json"

            import io
            from contextlib import redirect_stdout

            f = io.StringIO()
            with redirect_stdout(f):
                L.cmd_search(Args())

            import json
            data = json.loads(f.getvalue())
            assert len(data) == 1
            assert data[0]["snippet"] == "hello world"
