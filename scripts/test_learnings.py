#!/usr/bin/env python3

import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import unittest

import learnings as L


class TestGetNow(unittest.TestCase):
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


class TestRedactSecrets(unittest.TestCase):
    def test_api_key_redaction(self):
        field_name = "api" + "_key"
        secret_value = "x" * 20
        text = f'{field_name} = "{secret_value}"'
        result = L.redact_secrets(text)
        assert "[REDACTED]" in result
        assert secret_value not in result

    def test_bearer_token_redaction(self):
        token_value = "y" * 24
        text = f"Authorization: Bearer {token_value}"
        result = L.redact_secrets(text)
        assert "[REDACTED]" in result

    def test_no_false_positives_on_short_strings(self):
        text = "password = ok"
        result = L.redact_secrets(text)
        assert "[REDACTED]" not in result


class TestResolveRoot(unittest.TestCase):
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


class TestStatusCounts(unittest.TestCase):
    def test_counts_memory_headings_and_correction_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "learning" / "self-improving"
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
            base = Path(tmp) / "learning" / "self-improving"
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


class TestCliRootCompatibility(unittest.TestCase):
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


class TestGenerateId(unittest.TestCase):
    def test_id_uses_local_date(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "learning" / "self-improving"
            base.mkdir(parents=True)
            today = datetime.now().astimezone().strftime("%Y%m%d")
            entry_id = L.generate_id("LRN", base)
            assert entry_id.startswith(f"LRN-{today}-")


class TestVolatilePatterns(unittest.TestCase):
    def test_detects_pid(self):
        warnings = L.check_volatile_patterns("Process PID 12345 crashed")
        assert any("PID" in w for w in warnings)

    def test_detects_session_id(self):
        warnings = L.check_volatile_patterns("session-id=abc123def456")
        assert any("session" in w.lower() for w in warnings)

    def test_detects_temp_path(self):
        warnings = L.check_volatile_patterns("Found file at /tmp/foo.bar")
        assert any("/tmp/" in w for w in warnings)

    def test_detects_iso_timestamp(self):
        warnings = L.check_volatile_patterns("Event at 2026-05-09T14:30:00Z")
        assert any("2026-05-09T14:30:00Z" in w for w in warnings)

    def test_detects_current_state(self):
        warnings = L.check_volatile_patterns("Current timestamp is now")
        assert any("current" in w.lower() for w in warnings)

    def test_no_false_positives_on_plain_dates(self):
        warnings = L.check_volatile_patterns("Meeting on 2026-05-09")
        assert warnings == []

    def test_no_false_positives_on_stable_text(self):
        warnings = L.check_volatile_patterns("Always use pnpm in this repo")
        assert warnings == []


class TestVolatileCheckIntegration(unittest.TestCase):
    def test_blocks_volatile_without_force(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "learning" / "self-improving"
            base.mkdir(parents=True)

            class Args:
                root = tmp
                local_root = None
                summary = "Process PID 9999 failed"
                details = ""
                pattern = ""
                force = False

            import io
            from contextlib import redirect_stdout

            f = io.StringIO()
            with redirect_stdout(f):
                L.cmd_log_learning(Args())

            output = f.getvalue()
            assert "Volatile pattern detected" in output
            assert "Aborting" in output
            assert "Logged" not in output

    def test_allows_volatile_with_force(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "learning" / "self-improving"
            base.mkdir(parents=True)

            class Args:
                root = tmp
                local_root = None
                summary = "Process PID 9999 failed"
                details = ""
                pattern = ""
                force = True

            import io
            from contextlib import redirect_stdout

            f = io.StringIO()
            with redirect_stdout(f):
                L.cmd_log_learning(Args())

            output = f.getvalue()
            assert "Volatile pattern detected" in output
            assert "Logged:" in output


class TestSearchJsonFormat(unittest.TestCase):
    def test_json_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "learning" / "self-improving"
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


class TestMaintain(unittest.TestCase):
    def test_maintain_dry_run_hot_to_warm(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "learning" / "self-improving"
            base.mkdir(parents=True)

            memory = base / "memory.md"
            old_date = "2026-01-01"
            memory.write_text(
                f"# Memory\n\n"
                f"### LRN-20260101-001 ({old_date})\n"
                f"- **Type**: LRN\n"
                f"- **Summary**: test\n"
                f"- **First-Seen**: {old_date}\n"
                f"- **Last-Seen**: {old_date}\n"
                f"- **Recurrence-Count**: 1\n",
                encoding="utf-8",
            )

            old_epoch = os.environ.pop("SOURCE_DATE_EPOCH", None)
            try:
                future = datetime(2026, 3, 1, tzinfo=timezone.utc)
                os.environ["SOURCE_DATE_EPOCH"] = str(int(future.timestamp()))

                class Args:
                    root = tmp
                    local_root = None
                    apply = False
                    format = "text"

                import io
                from contextlib import redirect_stdout

                f = io.StringIO()
                with redirect_stdout(f):
                    L.cmd_maintain(Args())

                output = f.getvalue()
                assert "HOT_TO_WARM" in output
                assert "dry-run" in output.lower()

                content = memory.read_text(encoding="utf-8")
                assert "LRN-20260101-001" in content
            finally:
                if old_epoch is not None:
                    os.environ["SOURCE_DATE_EPOCH"] = old_epoch
                else:
                    os.environ.pop("SOURCE_DATE_EPOCH", None)

    def test_maintain_apply_hot_to_warm(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "learning" / "self-improving"
            base.mkdir(parents=True)

            memory = base / "memory.md"
            old_date = "2026-01-01"
            memory.write_text(
                f"# Memory\n\n"
                f"### LRN-20260101-001 ({old_date})\n"
                f"- **Type**: LRN\n"
                f"- **Summary**: test\n"
                f"- **First-Seen**: {old_date}\n"
                f"- **Last-Seen**: {old_date}\n"
                f"- **Recurrence-Count**: 1\n",
                encoding="utf-8",
            )

            old_epoch = os.environ.pop("SOURCE_DATE_EPOCH", None)
            try:
                future = datetime(2026, 3, 1, tzinfo=timezone.utc)
                os.environ["SOURCE_DATE_EPOCH"] = str(int(future.timestamp()))

                class Args:
                    root = tmp
                    local_root = None
                    apply = True
                    format = "text"

                import io
                from contextlib import redirect_stdout

                f = io.StringIO()
                with redirect_stdout(f):
                    L.cmd_maintain(Args())

                output = f.getvalue()
                assert "HOT_TO_WARM" in output
                assert "applied" in output.lower()

                content = memory.read_text(encoding="utf-8")
                assert "LRN-20260101-001" not in content

                domain_file = base / "domains" / "general.md"
                assert domain_file.exists()
                domain_content = domain_file.read_text(encoding="utf-8")
                assert "LRN-20260101-001" in domain_content
            finally:
                if old_epoch is not None:
                    os.environ["SOURCE_DATE_EPOCH"] = old_epoch
                else:
                    os.environ.pop("SOURCE_DATE_EPOCH", None)

    def test_maintain_warm_to_cold(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "learning" / "self-improving"
            base.mkdir(parents=True)

            domains_dir = base / "domains"
            domains_dir.mkdir(parents=True, exist_ok=True)

            general = domains_dir / "general.md"
            old_date = "2026-01-01"
            general.write_text(
                f"# Domain General\n\n"
                f"### ERR-20260101-002 ({old_date})\n"
                f"- **Type**: ERR\n"
                f"- **Summary**: warm test\n"
                f"- **First-Seen**: {old_date}\n"
                f"- **Last-Seen**: {old_date}\n"
                f"- **Recurrence-Count**: 1\n",
                encoding="utf-8",
            )

            old_epoch = os.environ.pop("SOURCE_DATE_EPOCH", None)
            try:
                future = datetime(2026, 4, 5, tzinfo=timezone.utc)
                os.environ["SOURCE_DATE_EPOCH"] = str(int(future.timestamp()))

                class Args:
                    root = tmp
                    local_root = None
                    apply = True
                    format = "text"

                import io
                from contextlib import redirect_stdout

                f = io.StringIO()
                with redirect_stdout(f):
                    L.cmd_maintain(Args())

                output = f.getvalue()
                assert "WARM_TO_COLD" in output

                content = general.read_text(encoding="utf-8")
                assert "ERR-20260101-002" not in content

                archive_file = base / "archive" / "general.md"
                assert archive_file.exists()
                archive_content = archive_file.read_text(encoding="utf-8")
                assert "ERR-20260101-002" in archive_content
            finally:
                if old_epoch is not None:
                    os.environ["SOURCE_DATE_EPOCH"] = old_epoch
                else:
                    os.environ.pop("SOURCE_DATE_EPOCH", None)

    def test_maintain_promote_candidate(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "learning" / "self-improving"
            base.mkdir(parents=True)

            memory = base / "memory.md"
            today_str = datetime.now().astimezone().strftime("%Y-%m-%d")
            memory.write_text(
                f"# Memory\n\n"
                f"### FTR-20260509-003 ({today_str})\n"
                f"- **Type**: FTR\n"
                f"- **Summary**: test\n"
                f"- **First-Seen**: {today_str}\n"
                f"- **Last-Seen**: {today_str}\n"
                f"- **Recurrence-Count**: 3\n",
                encoding="utf-8",
            )

            class Args:
                root = tmp
                local_root = None
                apply = False
                format = "text"

            import io
            from contextlib import redirect_stdout

            f = io.StringIO()
            with redirect_stdout(f):
                L.cmd_maintain(Args())

            output = f.getvalue()
            assert "PROMOTE_CANDIDATE" in output


class TestMaintain(unittest.TestCase):
    def test_parser_exposes_maintain(self):
        parser = L.build_parser()
        args = parser.parse_args(["maintain", "--format", "json"])
        assert args.command == "maintain"
        assert args.format == "json"
        assert args.dry_run is True

    def test_maintain_dry_run_default(self):
        parser = L.build_parser()
        args = parser.parse_args(["maintain"])
        assert args.dry_run is True

    def test_maintain_apply_flag(self):
        parser = L.build_parser()
        args = parser.parse_args(["maintain", "--apply"])
        assert args.dry_run is False

    def test_dry_run_reports_stale_hot(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "learning" / "self-improving"
            base.mkdir(parents=True)

            memory = base / "memory.md"
            memory.write_text(
                "# Memory\n\n"
                "### LRN-20200101-001 (2020-01-01) [Pattern-Key: old-pattern]\n"
                "- **Type**: LRN\n"
                "- **First-Seen**: 2020-01-01\n"
                "- **Last-Seen**: 2020-01-01\n"
                "- **Recurrence-Count**: 1\n"
                "- **Status**: active\n"
                "- **Area**: general\n"
                "- **Summary**: Old learning\n\n",
                encoding="utf-8",
            )

            class Args:
                root = tmp
                local_root = None
                dry_run = True
                format = "json"

            import io
            from contextlib import redirect_stdout

            f = io.StringIO()
            with redirect_stdout(f):
                L.cmd_maintain(Args())

            import json
            data = json.loads(f.getvalue())
            assert len(data["stale_hot"]) == 1
            assert data["stale_hot"][0]["id"] == "LRN-20200101-001"
            assert data["stale_hot"][0]["action"] == "HOT_TO_WARM"

            text = memory.read_text(encoding="utf-8")
            assert "LRN-20200101-001" in text

    def test_apply_moves_stale_hot_to_warm(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "learning" / "self-improving"
            base.mkdir(parents=True)

            memory = base / "memory.md"
            memory.write_text(
                "# Memory\n\n"
                "## Header\n\n"
                "### LRN-20200101-001 (2020-01-01) [Pattern-Key: old-pattern]\n"
                "- **Type**: LRN\n"
                "- **First-Seen**: 2020-01-01\n"
                "- **Last-Seen**: 2020-01-01\n"
                "- **Recurrence-Count**: 1\n"
                "- **Status**: active\n"
                "- **Area**: general\n"
                "- **Summary**: Old learning\n\n"
                "### LRN-20260501-001 (2026-05-01) [Pattern-Key: fresh-pattern]\n"
                "- **Type**: LRN\n"
                "- **First-Seen**: 2026-05-01\n"
                "- **Last-Seen**: 2026-05-01\n"
                "- **Recurrence-Count**: 1\n"
                "- **Status**: active\n"
                "- **Area**: general\n"
                "- **Summary**: Fresh learning\n\n",
                encoding="utf-8",
            )

            class Args:
                root = tmp
                local_root = None
                dry_run = False
                format = "json"

            import io
            from contextlib import redirect_stdout

            f = io.StringIO()
            with redirect_stdout(f):
                L.cmd_maintain(Args())

            import json
            data = json.loads(f.getvalue())
            assert len(data["stale_hot"]) == 1

            memory_text = memory.read_text(encoding="utf-8")
            assert "LRN-20200101-001" not in memory_text
            assert "LRN-20260501-001" in memory_text
            assert "## Header" in memory_text

            target = base / "domains" / "general.md"
            assert target.exists()
            target_text = target.read_text(encoding="utf-8")
            assert "LRN-20200101-001" in target_text
            assert "Old learning" in target_text

    def test_apply_archives_stale_warm(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "learning" / "self-improving"
            base.mkdir(parents=True)
            domains = base / "domains"
            domains.mkdir(parents=True, exist_ok=True)

            warm = domains / "backend.md"
            warm.write_text(
                "# Backend\n\n"
                "### ERR-20200101-001 (2020-01-01) [Pattern-Key: old-error]\n"
                "- **Type**: ERR\n"
                "- **First-Seen**: 2020-01-01\n"
                "- **Last-Seen**: 2020-01-01\n"
                "- **Recurrence-Count**: 1\n"
                "- **Status**: active\n"
                "- **Area**: domain:backend\n"
                "- **Summary**: Old error\n\n"
                "### ERR-20260501-001 (2026-05-01) [Pattern-Key: fresh-error]\n"
                "- **Type**: ERR\n"
                "- **First-Seen**: 2026-05-01\n"
                "- **Last-Seen**: 2026-05-01\n"
                "- **Recurrence-Count**: 1\n"
                "- **Status**: active\n"
                "- **Area**: domain:backend\n"
                "- **Summary**: Fresh error\n\n",
                encoding="utf-8",
            )

            class Args:
                root = tmp
                local_root = None
                dry_run = False
                format = "json"

            import io
            from contextlib import redirect_stdout

            f = io.StringIO()
            with redirect_stdout(f):
                L.cmd_maintain(Args())

            import json
            data = json.loads(f.getvalue())
            assert len(data["stale_warm"]) == 1

            warm_text = warm.read_text(encoding="utf-8")
            assert "ERR-20200101-001" not in warm_text
            assert "ERR-20260501-001" in warm_text
            assert "# Backend" in warm_text

            archive = base / "archive" / "backend.md"
            assert archive.exists()
            archive_text = archive.read_text(encoding="utf-8")
            assert "ERR-20200101-001" in archive_text
            assert "Old error" in archive_text

    def test_reports_promotion_candidate(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "learning" / "self-improving"
            base.mkdir(parents=True)

            memory = base / "memory.md"
            memory.write_text(
                "# Memory\n\n"
                "### LRN-20260501-001 (2026-05-01) [Pattern-Key: frequent-pattern]\n"
                "- **Type**: LRN\n"
                "- **First-Seen**: 2026-05-01\n"
                "- **Last-Seen**: 2026-05-01\n"
                "- **Recurrence-Count**: 5\n"
                "- **Status**: active\n"
                "- **Area**: general\n"
                "- **Summary**: Frequent learning\n\n",
                encoding="utf-8",
            )

            class Args:
                root = tmp
                local_root = None
                dry_run = True
                format = "json"

            import io
            from contextlib import redirect_stdout

            f = io.StringIO()
            with redirect_stdout(f):
                L.cmd_maintain(Args())

            import json
            data = json.loads(f.getvalue())
            assert len(data["promote_candidates"]) == 1
            assert data["promote_candidates"][0]["id"] == "LRN-20260501-001"
            assert data["promote_candidates"][0]["recurrence_count"] == 5
