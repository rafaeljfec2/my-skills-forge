"""v0.2 hardening tests: developer report, judge isolation, memory sync."""

from __future__ import annotations

import json
import shlex
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import support
from connexto_workflow.engine import Engine
from connexto_workflow.errors import PolicyError, PreconditionError
from connexto_workflow.workflow_defaults import default_workflow

_BACKENDS = SCRIPTS / "backends"


class DeveloperContractTests(unittest.TestCase):
    def test_empty_implement_command_requires_report(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            repo = Path(raw)
            support.seed_passing(repo)
            engine = support.open_run(repo, "FEAT-010", "FEATURE")
            support.fill_plan(engine)
            with self.assertRaises(PreconditionError):
                engine.run_implement_hook("developer", "dev-1")
            engine.note_implementation("developer", "dev-1", "Only a note.")
            with self.assertRaises(PreconditionError):
                engine.run_validation("developer", "dev-1")

    def test_developer_backend_writes_repo_files(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            repo = Path(raw)
            support.seed_passing(repo)
            payload = support.project_config(support.passing_command())
            workflow = payload["workflow"]
            assert isinstance(workflow, dict)
            workflow["developer_command"] = shlex.join(
                [sys.executable, str(_BACKENDS / "dev_worker.py")]
            )
            support.write_config(repo, payload)
            engine = support.open_run(repo, "FEAT-011", "FEATURE")
            support.fill_plan(engine)
            engine.run_developer_backend("developer", "dev-1", "dev-session-backend")
            report = engine.run_dir / "developer" / "report.json"
            self.assertTrue(report.is_file())
            self.assertTrue(engine.ensure().implementation_ready)


class ReviewerIsolationTests(unittest.TestCase):
    def test_judge_blocks_done_on_critical(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            repo = Path(raw)
            support.seed_passing(repo)
            payload = support.project_config(support.passing_command())
            workflow = payload["workflow"]
            assert isinstance(workflow, dict)
            workflow["judge_command"] = shlex.join(
                [sys.executable, str(_BACKENDS / "judge_worker.py")]
            )
            support.write_config(repo, payload)
            engine = support.reach_review(support.open_run(repo, "FEAT-012", "FEATURE"))
            engine.run_independent_judge("reviewer", "rev-1", "review-session-1")
            self.assertEqual(engine.ensure().status, "DELIVERY")
            self.assertEqual(engine.ensure().reviewer_session_id, "review-session-1")

    def test_manual_review_rejected_when_judge_configured(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            repo = Path(raw)
            support.seed_passing(repo)
            payload = support.project_config(support.passing_command())
            workflow = payload["workflow"]
            assert isinstance(workflow, dict)
            workflow["judge_command"] = shlex.join([sys.executable, "-c", "print(1)"])
            support.write_config(repo, payload)
            engine = support.reach_review(support.open_run(repo, "FEAT-013", "FEATURE"))
            with self.assertRaises(PolicyError):
                engine.submit_review("reviewer", "rev-1", {"summary": "manual", "findings": []})


class MemorySyncTests(unittest.TestCase):
    def test_remote_memory_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            repo = Path(raw)
            support.seed_passing(repo)
            payload = support.project_config(support.passing_command())
            workflow = payload["workflow"]
            assert isinstance(workflow, dict)
            workflow["memory_write_command"] = shlex.join(
                [sys.executable, str(_BACKENDS / "memory_write_worker.py")]
            )
            workflow["memory_read_command"] = shlex.join(
                [sys.executable, str(_BACKENDS / "memory_read_worker.py")]
            )
            support.write_config(repo, payload)
            engine = support.reach_review(support.open_run(repo, "FEAT-014", "FEATURE"))
            engine.submit_review(
                "reviewer",
                "rev-1",
                {"summary": "Clear.", "findings": []},
            )
            engine.compose_delivery(
                "orchestrator",
                "orch-1",
                {
                    "problem_solved": "x",
                    "solution": "y",
                    "files_changed": "test_ok.py",
                    "limitations": "none",
                    "follow_ups": "none",
                },
            )
            engine.request_transition("MEMORY", "orchestrator", "orch-1", "delivery_recorded")
            engine.sync_memory("orchestrator", "orch-1")
            state = engine.ensure()
            self.assertEqual(state.status, "DONE")
            self.assertEqual(state.memory_remote_status, "confirmed")
            self.assertEqual(state.memory_page_id, "FEAT-014")


if __name__ == "__main__":
    unittest.main()
