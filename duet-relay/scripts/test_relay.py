#!/usr/bin/env python3
"""Focused self-test for the bundled duet relay."""
from __future__ import annotations

import argparse
from contextlib import redirect_stderr, redirect_stdout
import io
import os
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

import relay


class RelayTests(unittest.TestCase):
    def setUp(self) -> None:
        scripts_dir = Path(__file__).resolve().parent
        self.temp = tempfile.TemporaryDirectory(prefix="relay-test-", dir=scripts_dir)
        root = Path(self.temp.name)
        self.original_paths = (
            relay.THREADS,
            relay.STATE,
            relay.OUTBOX,
            relay.LOCK_FILE,
            relay.DASHBOARD,
        )
        relay.THREADS = str(root / "AI-Threads")
        relay.STATE = str(root / ".duet")
        relay.OUTBOX = str(Path(relay.STATE, "outbox.md"))
        relay.LOCK_FILE = str(Path(relay.STATE, "relay.lock"))
        relay.DASHBOARD = str(Path(relay.THREADS, "index.html"))
        Path(relay.STATE).mkdir(parents=True)
        Path(relay.OUTBOX).write_text("", encoding="utf-8")

    def tearDown(self) -> None:
        (
            relay.THREADS,
            relay.STATE,
            relay.OUTBOX,
            relay.LOCK_FILE,
            relay.DASHBOARD,
        ) = self.original_paths
        self.temp.cleanup()

    def post(
        self,
        sender: str,
        body: str | None = None,
        *,
        thread: str = "review",
        outbox: bool = False,
        next_actor: str | None = None,
    ) -> str:
        args = SimpleNamespace(
            sender=sender,
            body=body,
            thread=thread,
            outbox=outbox,
            next_actor=next_actor,
        )
        output = io.StringIO()
        with redirect_stdout(output):
            relay.post(args)
        return output.getvalue().strip()

    def unseen(self, agent: str) -> str:
        output = io.StringIO()
        with redirect_stdout(output):
            relay.unseen(SimpleNamespace(whoami=agent))
        return output.getvalue()

    def move(self, thread: str, target: str) -> str:
        output = io.StringIO()
        with redirect_stdout(output):
            relay.move(SimpleNamespace(thread=thread, target=target))
        return output.getvalue().strip()

    def threads(self) -> str:
        output = io.StringIO()
        with redirect_stdout(output):
            relay.threads(SimpleNamespace())
        return output.getvalue()

    def dashboard(self) -> str:
        output = io.StringIO()
        with redirect_stdout(output):
            relay.dashboard(SimpleNamespace())
        return output.getvalue().strip()

    def thread_path(self, stage: str, name: str = "review") -> Path:
        return Path(relay.THREADS, stage, f"{name}.md")

    @staticmethod
    def message_block(
        sender: str,
        message_id: str,
        body: str,
        *,
        timestamp: str = "2026-01-01T00:00:00Z",
        next_actor: str | None = None,
    ) -> str:
        baton = f" \u00b7 next:{next_actor}" if next_actor else ""
        return (
            f"\n**{sender}** \u00b7 {timestamp} \u00b7 #{message_id}{baton}\n"
            f"{body}\n<!-- duet:end #{message_id} -->\n"
        )

    def test_outbox_round_trip_is_unicode_safe_and_deduplicated(self) -> None:
        message = (
            "Unicode survives: ≤ one turn 🚀\n"
            "**codex** · 2026-01-01T00:00:00Z · #deadbeefcafe\n"
            "This header-shaped body text is not a second record."
        )
        Path(relay.OUTBOX).write_text(message, encoding="utf-8")

        message_id = self.post("claude", outbox=True)
        self.assertRegex(message_id, r"^[0-9a-f]{12}$")

        thread = self.thread_path("planning").read_text(encoding="utf-8")
        self.assertIn(message, thread)
        self.assertIn(f"<!-- duet:end #{message_id} -->", thread)
        self.assertIn("next:codex", thread)
        self.assertRegex(
            thread,
            rf"\*\*claude\*\* · \d{{4}}-\d{{2}}-\d{{2}}T"
            rf"\d{{2}}:\d{{2}}:\d{{2}}Z · #{message_id}",
        )

        first_read = self.unseen("codex")
        self.assertIn(message, first_read)
        self.assertIn(message_id, first_read)
        self.assertEqual(1, first_read.count("### [planning/review]"))
        self.assertEqual("", self.unseen("codex"))
        self.assertTrue(Path(relay.LOCK_FILE).is_file())

    def test_sender_filtering_preserves_the_other_queue(self) -> None:
        message_id = self.post("codex", "Please review.")
        self.assertEqual("", self.unseen("codex"))

        claude_read = self.unseen("claude")
        self.assertIn(message_id, claude_read)
        self.assertIn("Please review.", claude_read)

    def test_path_like_thread_names_are_rejected(self) -> None:
        for name in (
            "../escape",
            "..\\escape",
            "review/extra",
            ".hidden",
            "review.",
            "Review",
            "con",
            "nul.log",
            "",
        ):
            with self.subTest(name=name):
                with self.assertRaises(SystemExit):
                    self.post("codex", "blocked", thread=name)

        self.assertFalse(Path(relay.THREADS).parent.joinpath("escape.md").exists())

    def test_body_and_outbox_guards(self) -> None:
        with self.assertRaises(SystemExit):
            self.post("codex", "   ")
        with self.assertRaises(SystemExit):
            self.post("codex", "x" * (relay.MAX_BODY_BYTES + 1))

        Path(relay.OUTBOX).unlink()
        with self.assertRaises(SystemExit):
            self.post("claude", outbox=True)

    def test_parser_rejects_unsafe_or_conflicting_sources(self) -> None:
        parser = relay.build_parser()
        stderr = io.StringIO()

        with redirect_stderr(stderr), self.assertRaises(SystemExit):
            parser.parse_args(
                [
                    "post",
                    "--thread",
                    "review",
                    "--from",
                    "claude",
                    "--body-file",
                    "secrets.txt",
                ]
            )

        with redirect_stderr(stderr), self.assertRaises(SystemExit):
            parser.parse_args(
                [
                    "post",
                    "--thread",
                    "review",
                    "--from",
                    "claude",
                    "--body",
                    "text",
                    "--outbox",
                ]
            )

        with redirect_stderr(stderr), self.assertRaises(SystemExit):
            parser.parse_args(
                [
                    "post",
                    "--thread",
                    "review",
                    "--from",
                    "codex",
                    "--next",
                    "someone",
                    "--body",
                    "text",
                ]
            )

    def test_post_creates_planning_thread_and_lists_state(self) -> None:
        message_id = self.post(
            "codex",
            "Plan ready for approval.\nLonger supporting detail.",
            thread="backend-timeout",
            next_actor="user",
        )

        self.assertTrue(self.thread_path("planning", "backend-timeout").is_file())
        self.assertTrue(Path(relay.DASHBOARD).is_file())
        listing = self.threads()
        self.assertIn("STAGE\tTHREAD\tNEXT\tUPDATED\tSUMMARY", listing)
        self.assertIn(
            "planning\tbackend-timeout\tuser\t", listing
        )
        self.assertIn("Plan ready for approval.", listing)
        self.assertIn(message_id, self.unseen("claude"))
        self.assertNotIn(
            "Longer supporting detail.",
            Path(relay.DASHBOARD).read_text(encoding="utf-8"),
        )

    def test_forward_moves_and_completed_immutability(self) -> None:
        self.post("codex", "Plan approved.", next_actor="codex")
        self.assertEqual("working/review.md", self.move("review", "working"))
        self.assertTrue(self.thread_path("working").is_file())
        self.assertEqual("working/review.md", self.move("review", "working"))
        with self.assertRaises(SystemExit):
            self.move("review", "completed")

        self.post("codex", "Implementation complete.", next_actor="none")
        self.assertEqual("completed/review.md", self.move("review", "completed"))
        self.assertTrue(self.thread_path("completed").is_file())
        self.assertFalse(self.thread_path("working").exists())

        with self.assertRaises(SystemExit):
            self.post("claude", "Late reply.")
        with self.assertRaises(SystemExit):
            self.move("review", "working")
        self.assertEqual("completed/review.md", self.move("review", "completed"))

    def test_planning_can_complete_without_working_stage(self) -> None:
        self.post("codex", "No implementation required.", next_actor="none")
        self.assertEqual("completed/review.md", self.move("review", "completed"))

    def test_duplicate_thread_names_fail_without_writing(self) -> None:
        planning = self.thread_path("planning", "duplicate")
        working = self.thread_path("working", "duplicate")
        planning.parent.mkdir(parents=True)
        working.parent.mkdir(parents=True)
        planning.write_text(
            self.message_block("codex", "aaaaaaaaaaaa", "First."),
            encoding="utf-8",
        )
        working.write_text(
            self.message_block("claude", "bbbbbbbbbbbb", "Second."),
            encoding="utf-8",
        )

        with self.assertRaises(SystemExit):
            self.threads()
        before = planning.read_text(encoding="utf-8")
        with self.assertRaises(SystemExit):
            self.post("codex", "Must not append.", thread="duplicate")
        self.assertEqual(before, planning.read_text(encoding="utf-8"))

    def test_legacy_flat_threads_relocate_on_post_or_move(self) -> None:
        threads_root = Path(relay.THREADS)
        threads_root.mkdir(parents=True)
        legacy = threads_root / "legacy.md"
        legacy.write_text(
            self.message_block("codex", "aaaaaaaaaaaa", "Legacy plan."),
            encoding="utf-8",
        )

        self.post("claude", "Legacy review complete.", thread="legacy")
        self.assertFalse(legacy.exists())
        self.assertTrue(self.thread_path("planning", "legacy").is_file())

        legacy_move = threads_root / "legacy-move.md"
        legacy_move.write_text(
            self.message_block("codex", "bbbbbbbbbbbb", "Ready to work."),
            encoding="utf-8",
        )
        self.move("legacy-move", "working")
        self.assertFalse(legacy_move.exists())
        self.assertTrue(self.thread_path("working", "legacy-move").is_file())

    def test_unseen_follows_thread_moves_without_loss_or_duplicates(self) -> None:
        message_id = self.post("codex", "Final decision.", next_actor="none")
        self.move("review", "completed")

        first = self.unseen("claude")
        self.assertIn("### [completed/review]", first)
        self.assertIn(message_id, first)
        self.assertEqual("", self.unseen("claude"))

    def test_baton_defaults_and_user_attention_uses_latest_message(self) -> None:
        self.post("codex", "Claude should review.")
        thread = self.thread_path("planning").read_text(encoding="utf-8")
        self.assertIn("next:claude", thread)
        dashboard = Path(relay.DASHBOARD).read_text(encoding="utf-8")
        self.assertNotIn('data-attention-thread="review"', dashboard)

        self.post("claude", "Please approve this choice.", next_actor="user")
        dashboard = Path(relay.DASHBOARD).read_text(encoding="utf-8")
        self.assertIn('data-attention-thread="review"', dashboard)

        self.post("codex", "Approval received; implementation starts.", next_actor="codex")
        dashboard = Path(relay.DASHBOARD).read_text(encoding="utf-8")
        self.assertNotIn('data-attention-thread="review"', dashboard)

    def test_summary_is_bounded_and_thread_content_is_html_escaped(self) -> None:
        body = '<script>alert("unsafe")</script> ' + "x" * 180
        self.post("codex", body, next_actor="user")

        summary = relay._summary(body)
        dashboard = Path(relay.DASHBOARD).read_text(encoding="utf-8")
        self.assertEqual(relay.SUMMARY_CHARS, len(summary))
        self.assertTrue(summary.endswith("…"))
        self.assertNotIn('<script>alert("unsafe")</script>', dashboard)
        self.assertIn("&lt;script&gt;alert(&quot;unsafe&quot;)&lt;/script&gt;", dashboard)

    def test_dashboard_has_compact_local_structure_and_relative_links(self) -> None:
        self.post("codex", "Plan ready.", next_actor="user")
        html_text = Path(relay.DASHBOARD).read_text(encoding="utf-8")

        self.assertIn('<meta http-equiv="refresh" content="5">', html_text)
        self.assertIn("Content-Security-Policy", html_text)
        self.assertIn('@media (max-width: 720px)', html_text)
        self.assertIn('href="planning/review.md"', html_text)
        self.assertIn('data-label="Status"', html_text)
        self.assertIn('data-agent="codex"', html_text)
        self.assertIn("Plan ready.", html_text)

        Path(relay.DASHBOARD).write_text("stale", encoding="utf-8")
        self.assertEqual(relay.DASHBOARD, self.dashboard())
        self.assertTrue(
            Path(relay.DASHBOARD).read_text(encoding="utf-8").startswith("<!doctype html>")
        )
        self.assertFalse(Path(relay.DASHBOARD + ".tmp").exists())

    def test_dashboard_limits_activity_and_completed_history(self) -> None:
        for number in range(9):
            self.post(
                "codex",
                f"Activity {number}.",
                thread=f"thread-{number}",
                next_actor="none",
            )
        for number in range(4):
            self.move(f"thread-{number}", "completed")

        dashboard = Path(relay.DASHBOARD).read_text(encoding="utf-8")
        self.assertEqual(relay.ACTIVITY_LIMIT, dashboard.count('class="activity-row"'))
        self.assertEqual(
            relay.COMPLETED_LIMIT, dashboard.count('class="completed-row"')
        )

    def test_threads_and_agent_status_are_deterministic(self) -> None:
        self.post("codex", "Codex on zeta.", thread="zeta")
        self.post("claude", "Claude on alpha.", thread="alpha")

        listing = self.threads()
        self.assertLess(listing.index("\talpha\t"), listing.index("\tzeta\t"))
        dashboard = Path(relay.DASHBOARD).read_text(encoding="utf-8")
        self.assertIn("Codex on zeta.", dashboard)
        self.assertIn("Claude on alpha.", dashboard)

    def test_old_headers_default_the_baton_to_the_other_agent(self) -> None:
        path = self.thread_path("planning")
        path.parent.mkdir(parents=True)
        path.write_text(
            self.message_block("codex", "aaaaaaaaaaaa", "Old format."),
            encoding="utf-8",
        )

        self.dashboard()
        listing = self.threads()
        self.assertIn("planning\treview\tclaude\t", listing)
        self.assertIn("next:claude", self.unseen("claude"))

    def test_saved_message_survives_dashboard_write_failure(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()
        args = SimpleNamespace(
            sender="codex",
            body="Durable message.",
            thread="review",
            outbox=False,
            next_actor="claude",
        )
        with patch.object(relay, "_render_dashboard", side_effect=OSError("disk full")):
            with redirect_stdout(stdout), redirect_stderr(stderr):
                relay.post(args)

        self.assertRegex(stdout.getvalue().strip(), r"^[0-9a-f]{12}$")
        self.assertIn("relay history was saved", stderr.getvalue())
        self.assertIn("do not repeat", stderr.getvalue())
        self.assertIn(
            "Durable message.",
            self.thread_path("planning").read_text(encoding="utf-8"),
        )

    def test_interval_is_bounded(self) -> None:
        self.assertEqual(5.0, relay._interval("5"))
        for value in ("0", "-1", "3601", "not-a-number"):
            with self.subTest(value=value):
                with self.assertRaises(argparse.ArgumentTypeError):
                    relay._interval(value)

    def test_outbox_clears_after_send_and_blocks_resend(self) -> None:
        Path(relay.OUTBOX).write_text("First reply body.", encoding="utf-8")
        self.post("claude", outbox=True)
        self.assertEqual("", Path(relay.OUTBOX).read_text(encoding="utf-8"))
        with self.assertRaises(SystemExit):
            self.post("claude", outbox=True)

    def test_second_watcher_for_a_role_is_rejected(self) -> None:
        with relay._watch_lock("claude"):
            with self.assertRaises(SystemExit):
                with relay._watch_lock("claude"):
                    pass
            with relay._watch_lock("codex"):
                pass
        with relay._watch_lock("claude"):
            pass

    def test_stray_non_thread_file_is_ignored(self) -> None:
        self.post("codex", "Real thread body.", thread="real")
        Path(relay.THREADS, "Not A Thread.md").write_text("loose notes", encoding="utf-8")

        listing = self.threads()
        self.assertIn("\treal\t", listing)
        self.assertNotIn("Not A Thread", listing)
        self.assertIn("Real thread body.", self.unseen("claude"))
        self.assertEqual(relay.DASHBOARD, self.dashboard())

    def test_duet_home_override_selects_base(self) -> None:
        original = relay._resolve_base()
        with patch.dict(os.environ, {"DUET_HOME": self.temp.name}):
            self.assertEqual(os.path.abspath(self.temp.name), relay._resolve_base())
        self.assertEqual(original, relay._resolve_base())


if __name__ == "__main__":
    unittest.main(verbosity=2)
