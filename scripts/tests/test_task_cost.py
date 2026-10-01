"""Tests for scripts/task_cost.py. Run: python3 -m unittest discover scripts/tests"""

import contextlib
import io
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import task_cost  # noqa: E402

OLD = "aaaabbbb-0000-0000-0000-000000000000"
LATEST = "ccccdddd-0000-0000-0000-000000000000"
CURRENT = "eeeeffff-0000-0000-0000-000000000000"
T0 = 1790679600000  # 2026-09-29 11:00:00 UTC, in ms

TASK = """---
id: M9-01
epic: Testing
title: Fixture task
---

# M9-01 · Fixture task

The script owns everything below `<!-- task-cost -->`.

<!-- task-cost -->
"""

CLEAR = {"type": "user", "message": {"role": "user", "content": "<command-name>/clear</command-name>"}}


def usage(inp, out, read, write):
    return {
        "inputTokens": inp,
        "outputTokens": out,
        "thinkingTokens": 7,
        "cacheReadInputTokens": read,
        "cacheCreationInputTokens": write,
        "webSearchRequests": 0,
        "costUSD": 0.5,
    }


def cost_state(session_id, start_ms, duration_ms, models):
    return {
        "type": "cost-state",
        "sessionId": session_id,
        "startTime": start_ms,
        "totalDuration": duration_ms,
        "modelUsage": models,
    }


class TaskCostTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        self.repo = self.tmp / "my.repo"
        self.task = self.repo / "docs" / "tasks" / "M9" / "testing" / "M9-01-task.md"
        self.task.parent.mkdir(parents=True)
        self.task.write_text(TASK)
        self.proj = task_cost.project_dir(self.tmp / "projects", str(self.repo.resolve()))
        self.proj.mkdir(parents=True)
        # an older ended session, the one that just ended (with a stale cost-state
        # before the final one), and the current session, which has none yet
        self.write(OLD, CLEAR, cost_state(OLD, T0 - 3_600_000, 60_000, {"claude-opus-5-5": usage(1, 1, 1, 1)}))
        self.write(
            LATEST,
            CLEAR,
            cost_state(LATEST, T0, 1_000, {"claude-opus-5-5": usage(9, 9, 9, 9)}),
            cost_state(
                LATEST,
                T0,
                180_500,
                {
                    "claude-opus-5-5": usage(16, 72, 1003, 469),
                    "claude-haiku-4-5-20251001": usage(100, 200, 0, 30),
                    "claude-sonnet-5-5": usage(0, 0, 0, 0),
                },
            ),
        )
        self.write(CURRENT, CLEAR)

    def write(self, session_id, *entries):
        path = self.proj / f"{session_id}.jsonl"
        path.write_text("".join(json.dumps(e) + "\n" for e in entries) + "{partial")

    def run_script(self, *args):
        err = io.StringIO()
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(err):
            task_cost.main([*args, "--repo", str(self.repo), "--projects-dir", str(self.tmp / "projects")])
        return err.getvalue()

    def rows(self):
        return task_cost.parse_rows(self.task.read_text().rsplit(task_cost.MARKER, 1)[1])

    def test_project_dir_replaces_non_alphanumerics(self):
        got = task_cost.project_dir(Path("/p"), "/Users/g.s/dnd-keep")
        self.assertEqual(got, Path("/p/-Users-g-s-dnd-keep"))

    def test_picks_most_recently_ended_session_and_its_last_cost_state(self):
        session_id, state = task_cost.ended_session(self.proj, CURRENT, None)
        self.assertEqual(session_id, LATEST)
        got = task_cost.session_usage(session_id, state)
        self.assertEqual(
            got["models"],
            {
                "claude-opus-5-5": {"input": 16, "output": 72, "cache_read": 1003, "cache_write": 469},
                "claude-haiku-4-5-20251001": {"input": 100, "output": 200, "cache_read": 0, "cache_write": 30},
                # models with no tokens are dropped
            },
        )
        self.assertEqual(got["seconds"], 180)
        self.assertEqual(got["session"], "ccccdddd")

    def test_writes_footer_by_id(self):
        err = self.run_script("M9-01", CURRENT)
        self.assertEqual(err, "")
        text = self.task.read_text()
        # the inline mention of the marker in the body is left alone
        self.assertTrue(text.startswith(TASK.rsplit(task_cost.MARKER, 1)[0]))
        self.assertIn("| `ccccdddd` | 2026-09-29 11:00 | 3m 00s | claude-opus-5-5 | 16 | 72 | 1,003 | 469 |", text)
        self.assertIn("| **Total** | | 3m 00s | claude-opus-5-5 | **16** | **72** | **1,003** | **469** |", text)
        self.assertEqual(len(self.rows()), 2)

    def test_rerun_same_session_does_not_double_count(self):
        self.run_script("M9-01", CURRENT)
        first = self.task.read_text()
        self.run_script("M9-01", CURRENT)
        self.assertEqual(self.task.read_text(), first)

    def test_explicit_session_adds_rows_and_totals(self):
        self.run_script("M9-01", CURRENT)
        self.run_script(str(self.task), CURRENT, "--session", OLD)  # by path this time
        text = self.task.read_text()
        self.assertEqual(len(self.rows()), 3)
        self.assertIn("| `aaaabbbb` | 2026-09-29 10:00 | 1m 00s | claude-opus-5-5 | 1 | 1 | 1 | 1 |", text)
        self.assertIn("| **Total** | | 4m 00s | claude-opus-5-5 | **17** | **73** | **1,004** | **470** |", text)
        self.assertIn("| **Total** | | 4m 00s | claude-haiku-4-5-20251001 | **100** | **200** | **0** | **30** |", text)

    def test_explicit_session_that_has_not_ended_fails(self):
        with self.assertRaises(SystemExit):
            self.run_script("M9-01", OLD, "--session", CURRENT)

    def test_warns_when_current_session_did_not_start_with_clear(self):
        self.write(CURRENT, {"type": "user", "message": {"role": "user", "content": "hi"}})
        self.assertIn("didn't start with /clear", self.run_script("M9-01", CURRENT))

    def test_appends_marker_if_missing_and_warns_on_id_mismatch(self):
        self.task.write_text(TASK.replace("id: M9-01", "id: M9-02").replace("\n<!-- task-cost -->\n", "\n"))
        err = self.run_script("M9-01", CURRENT)
        self.assertIn("doesn't match filename", err)
        text = self.task.read_text()
        self.assertIn(f"\n{task_cost.MARKER}\n", text)
        self.assertIn("The script owns everything below `<!-- task-cost -->`.", text)
        self.assertEqual(len(self.rows()), 2)

    def test_unknown_task_id_fails(self):
        with self.assertRaises(SystemExit):
            self.run_script("M9-99", CURRENT)


if __name__ == "__main__":
    unittest.main()
