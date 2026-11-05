"""Behavior tests for configuration, transitions, gates, recovery, and the proof run."""

from __future__ import annotations

import json
import shlex
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
SKILL = SCRIPTS.parent
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import support
from connexto_workflow.commands import run_command
from connexto_workflow.config import parse_config
from connexto_workflow.engine import Engine
from connexto_workflow.errors import ConfigError, InvalidTransition, PolicyError
from connexto_workflow.model import EDGES
from connexto_workflow.proof import run_proof
from connexto_workflow.redact import redact


class ConfigTests(unittest.TestCase):
    def test_accepts_explicit_null_stack(self) -> None:
        config = parse_config(support.project_config(support.passing_command(), language=None, framework=None))
        self.assertIsNone(config.project.language)
        self.assertIsNone(config.project.framework)
        self.assertEqual(config.required_commands()[0][0], "test")

    def test_rejects_missing_required_command(self) -> None:
        payload = support.project_config(support.passing_command())
        commands = payload["commands"]
        self.assertIsInstance(commands, dict)
        commands["test"] = None
        with self.assertRaises(ConfigError):
            parse_config(payload)

    def test_rejects_unknown_keys_and_empty_gates(self) -> None:
        payload = support.project_config(support.passing_command())
        payload["extra"] = True
        with self.assertRaises(ConfigError):
            parse_config(payload)
        empty = support.project_config(support.passing_command())
        quality = empty["quality"]
        self.assertIsInstance(quality, dict)
        quality["require_tests"] = False
        with self.assertRaises(ConfigError):
            parse_config(empty)

    def test_rejects_secret_shaped_command(self) -> None:
        payload = support.project_config("python3 -c 'print(1)'")
        commands = payload["commands"]
        self.assertIsInstance(commands, dict)
        commands["test"] = "python3 -c 'print(\"token=abc\")'"
        with self.assertRaises(ConfigError):
            parse_config(payload)

    def test_missing_file_does_not_assume_a_stack(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            repo = Path(raw)
            engine = Engine(repo, "FEAT-001")
            with self.assertRaises(ConfigError) as caught:
                engine.init_run(support.brief_for("FEAT-001", "FEATURE"))
            self.assertIn("does not assume", str(caught.exception))


class TransitionTests(unittest.TestCase):
    def test_rejects_undefined_and_gated_edges(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            repo = Path(raw)
            support.seed_passing(repo)
            engine = support.open_run(repo, "FEAT-001", "FEATURE")
            with self.assertRaises(InvalidTransition):
                engine.request_transition("DONE", "orchestrator", "orch-1", "start")
            support.fill_plan(engine)
            engine.note_implementation("developer", "dev-1", "Ready to validate.")
            with self.assertRaises(InvalidTransition):
                engine.request_transition("VALIDATE", "developer", "dev-1", "implementation_ready")
            self.assertEqual(engine.ensure().status, "IMPLEMENT")

    def test_research_and_plan_returns(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            repo = Path(raw)
            support.seed_passing(repo)
            engine = support.open_run(repo, "FEAT-001", "FEATURE")
            engine.put_artifact("researcher", "res-1", "research.md", _plan_research())
            engine.request_transition("RESEARCH", "orchestrator", "orch-1", "intake_complete")
            engine.request_transition("RESEARCH", "researcher", "res-1", "insufficient_research")
            self.assertEqual(engine.ensure().status, "RESEARCH")
            engine.request_transition("PLAN", "researcher", "res-1", "research_complete")
            engine.request_transition("PLAN", "planner", "plan-1", "inconsistent_plan")
            self.assertEqual(engine.ensure().status, "PLAN")

    def test_attempt_limit_fails_the_run(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            repo = Path(raw)
            support.seed_passing(repo, quality={"max_validate_attempts": 1})
            (repo / "test_ok.py").write_text("raise SystemExit(1)\n", encoding="utf-8")
            engine = support.open_run(repo, "FEAT-001", "FEATURE")
            support.fill_plan(engine)
            support.submit_sample_report(engine, "dev-1", "dev-session-1")
            engine.run_validation("developer", "dev-1")
            self.assertEqual(engine.ensure().status, "FAILED")
            self.assertEqual(engine.ensure().validate_failures, 1)

    def test_validation_failure_returns_to_implement(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            repo = Path(raw)
            support.seed_passing(repo, quality={"max_validate_attempts": 2})
            (repo / "test_ok.py").write_text("raise SystemExit(1)\n", encoding="utf-8")
            engine = support.open_run(repo, "FEAT-001", "FEATURE")
            support.fill_plan(engine)
            support.submit_sample_report(engine, "dev-1", "dev-session-1")
            engine.run_validation("developer", "dev-1")
            state = engine.ensure()
            self.assertEqual(state.status, "IMPLEMENT")
            self.assertEqual(state.validate_failures, 1)
            self.assertFalse(state.implementation_ready)
            self.assertFalse(state.last_validation_passed)

    def test_resume_reloads_the_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            repo = Path(raw)
            support.seed_passing(repo)
            engine = support.open_run(repo, "FEAT-001", "FEATURE")
            engine.put_artifact("researcher", "res-1", "research.md", _plan_research())
            engine.request_transition("RESEARCH", "orchestrator", "orch-1", "intake_complete")
            reloaded = Engine(repo, "FEAT-001")
            reloaded.load()
            self.assertEqual(reloaded.ensure().status, "RESEARCH")
            reloaded.request_transition("PLAN", "researcher", "res-1", "research_complete")
            self.assertEqual(reloaded.ensure().status, "PLAN")

    def test_runs_are_isolated(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            repo = Path(raw)
            support.seed_passing(repo)
            first = support.open_run(repo, "FEAT-001", "FEATURE")
            second = support.open_run(repo, "FEAT-002", "FEATURE")
            first.put_artifact("researcher", "res-1", "research.md", _plan_research())
            self.assertFalse((second.run_dir / "research.md").exists())
            self.assertNotEqual(first.run_dir, second.run_dir)

    def test_snapshot_survives_a_later_config_edit(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            repo = Path(raw)
            support.seed_passing(repo)
            support.open_run(repo, "FEAT-001", "FEATURE")
            (repo / "connexto.project.json").write_text("{", encoding="utf-8")
            reloaded = Engine(repo, "FEAT-001")
            reloaded.load()
            self.assertEqual(reloaded.ensure().target_project, "sample")


class PolicyTests(unittest.TestCase):
    def test_risk_cannot_be_lowered_and_hotfix_waits(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            repo = Path(raw)
            support.seed_passing(repo)
            engine = Engine(repo, "HOTFIX-001")
            with self.assertRaises(PolicyError):
                engine.init_run(support.brief_for("HOTFIX-001", "HOTFIX", "LOW"))
            engine.init_run(support.brief_for("HOTFIX-001", "HOTFIX"))
            self.assertEqual(engine.ensure().risk, "HIGH")
            engine.request_transition("INTAKE", "orchestrator", "orch-1", "start")
            engine.request_transition("RESEARCH", "orchestrator", "orch-1", "intake_complete")
            self.assertEqual(engine.ensure().status, "WAITING_APPROVAL")
            with self.assertRaises(PolicyError):
                engine.approve("orchestrator", "orch-1", "start_high_risk")
            engine.approve("orchestrator", "lead-1", "start_high_risk")
            self.assertEqual(engine.ensure().status, "RESEARCH")

    def test_protected_action_requires_a_different_approver(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            repo = Path(raw)
            support.seed_passing(repo)
            engine = support.open_run(repo, "FEAT-001", "FEATURE")
            engine.request_protected("orchestrator", "orch-1", "production_publish")
            self.assertEqual(engine.ensure().status, "WAITING_APPROVAL")
            engine.approve("orchestrator", "lead-1", "protected:production_publish")
            self.assertEqual(engine.ensure().status, "INTAKE")
            self.assertIn("protected:production_publish", engine.ensure().approvals)

    def test_reviewer_must_differ_and_medium_blocks_important(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            repo = Path(raw)
            support.seed_passing(repo)
            engine = support.reach_review(support.open_run(repo, "FEAT-001", "FEATURE"))
            self.assertEqual(engine.ensure().status, "REVIEW")
            with self.assertRaises(PolicyError):
                engine.submit_review("reviewer", "dev-1", {"summary": "same actor", "findings": []})
            self.assertEqual(engine.ensure().status, "REVIEW")
            engine.submit_review(
                "reviewer",
                "rev-1",
                {
                    "summary": "Important gap.",
                    "findings": [
                        {
                            "severity": "important",
                            "file": "test_ok.py",
                            "location": "test_ok",
                            "rationale": "The change does not state an error path.",
                            "return_to": "IMPLEMENT",
                        }
                    ],
                },
            )
            self.assertEqual(engine.ensure().status, "IMPLEMENT")
            self.assertFalse(engine.ensure().last_validation_passed)

    def test_low_risk_allows_important_findings(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            repo = Path(raw)
            support.seed_passing(repo)
            engine = support.reach_review(support.open_run(repo, "BUG-001", "BUGFIX"))
            self.assertEqual(engine.ensure().risk, "LOW")
            engine.submit_review(
                "reviewer",
                "rev-1",
                {
                    "summary": "Non-blocking note.",
                    "findings": [
                        {
                            "severity": "important",
                            "file": "test_ok.py",
                            "location": "test_ok",
                            "rationale": "Worth a follow-up, not a release block at LOW.",
                        }
                    ],
                },
            )
            self.assertEqual(engine.ensure().status, "DELIVERY")

    def test_unknown_role_does_not_move_the_run(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            repo = Path(raw)
            support.seed_passing(repo)
            engine = support.open_run(repo, "FEAT-001", "FEATURE")
            with self.assertRaises(PolicyError):
                engine.request_transition("RESEARCH", "intern", "orch-1", "intake_complete")
            self.assertEqual(engine.ensure().status, "INTAKE")

    def test_researcher_cannot_claim_implementation(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            repo = Path(raw)
            support.seed_passing(repo)
            engine = support.open_run(repo, "FEAT-001", "FEATURE")
            with self.assertRaises(PolicyError):
                engine.put_artifact("researcher", "res-1", "research.md", "Implemented: yes\n")

    def test_commit_refuses_base_branch_and_secret_content(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            repo = Path(raw)
            _git(repo, "init", "-b", "main")
            support.seed_passing(repo, git={"isolated_branch": False, "allow_commit": True})
            engine = support.open_run(repo, "FEAT-001", "FEATURE")
            support.fill_plan(engine)
            with self.assertRaises(PolicyError):
                engine.commit_work("developer", "dev-1", "should not land", ["test_ok.py"])
            isolated = Path(raw) / "isolated"
            _git(isolated, "init", "-b", "main")
            (isolated / "note.py").write_text("value = 1\n", encoding="utf-8")
            _git(isolated, "add", "note.py")
            _git(isolated, "commit", "-m", "base")
            support.seed_passing(isolated, git={"isolated_branch": True, "allow_commit": True})
            secret_run = support.open_run(isolated, "FEAT-001", "FEATURE")
            support.fill_plan(secret_run)
            (isolated / "note.py").write_text("token=supersecret\n", encoding="utf-8")
            with self.assertRaises(PolicyError):
                secret_run.commit_work("developer", "dev-1", "leak", ["note.py"])
            self.assertIsNone(secret_run.ensure().git_commit)

    def test_block_and_unblock_restore_the_same_state(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            repo = Path(raw)
            support.seed_passing(repo)
            engine = support.open_run(repo, "FEAT-001", "FEATURE")
            engine.block("orchestrator", "orch-1", "fixture database is down")
            self.assertEqual(engine.ensure().status, "BLOCKED")
            engine.unblock("orchestrator", "orch-1")
            self.assertEqual(engine.ensure().status, "INTAKE")


class CommandTests(unittest.TestCase):
    def test_records_exit_and_redacts_output(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            repo = Path(raw)
            log = repo / "commands.jsonl"
            command = shlex.join([sys.executable, "-c", "print('token=supersecret')"])
            record = run_command(repo, "leak", command, 10, log)
            self.assertEqual(record.exit_code, 0)
            body = log.read_text(encoding="utf-8")
            self.assertNotIn("supersecret", body)
            self.assertIn("[REDACTED]", body)
            self.assertNotIn("supersecret", redact("password=hunter2"))

    def test_timeout_is_a_recorded_result(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            repo = Path(raw)
            log = repo / "commands.jsonl"
            command = shlex.join([sys.executable, "-c", "import time; time.sleep(5)"])
            record = run_command(repo, "slow", command, 1, log)
            self.assertTrue(record.timed_out)
            self.assertIsNone(record.exit_code)
            self.assertFalse(record.passed)


class ProofTests(unittest.TestCase):
    def test_real_feature_resumes_after_reload(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            summary = run_proof(Path(raw) / "demo")
        self.assertEqual(summary["final_status"], "DONE")
        self.assertEqual(summary["resumed_status"], "DONE")
        self.assertEqual(summary["git_branch"], "connexto/FEAT-001")
        exits = summary["validate_exits"]
        self.assertIsInstance(exits, list)
        self.assertGreaterEqual(len(exits), 2)
        self.assertNotEqual(exits[0], 0)
        self.assertEqual(exits[-1], 0)
        self.assertTrue(summary["git_commit"])
        self.assertEqual(summary["memory_page"], "runs/FEAT-001.md")

    def test_cli_status_reads_the_same_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            repo = Path(raw)
            support.seed_passing(repo)
            cli = SCRIPTS / "cdw.py"
            init = subprocess.run(
                [
                    sys.executable,
                    str(cli),
                    "init",
                    "--repo",
                    str(repo),
                    "--demand-id",
                    "FEAT-009",
                    "--type",
                    "FEATURE",
                    "--problem",
                    "Need a checkpoint.",
                    "--outcome",
                    "Status survives a new process.",
                    "--scope",
                    "test_ok.py",
                    "--project",
                    "sample",
                    "--criterion",
                    "status prints FEAT-009",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(init.returncode, 0, init.stderr)
            status = subprocess.run(
                [sys.executable, str(cli), "status", "--repo", str(repo), "--run", "FEAT-009"],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(status.returncode, 0, status.stderr)
            payload = json.loads(status.stdout)
            self.assertEqual(payload["status"], "PENDING")
            self.assertEqual(payload["demand_id"], "FEAT-009")


class ContractTests(unittest.TestCase):
    def test_lifecycle_doc_lists_every_edge(self) -> None:
        text = (SKILL / "references" / "lifecycle.md").read_text(encoding="utf-8")
        for source, dest in EDGES:
            self.assertIn(f"{source} → {dest}", text)

    def test_delivery_cannot_be_composed_without_review(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            repo = Path(raw)
            support.seed_passing(repo)
            engine = support.reach_review(support.open_run(repo, "FEAT-001", "FEATURE"))
            with self.assertRaises(InvalidTransition):
                engine.compose_delivery(
                    "orchestrator",
                    "orch-1",
                    {
                        "problem_solved": "x",
                        "solution": "y",
                        "files_changed": "z",
                        "limitations": "none",
                        "follow_ups": "none",
                    },
                )


def _plan_research() -> str:
    return support.plan_parts()[0]


def _git(repo: Path, *args: str) -> None:
    repo.mkdir(parents=True, exist_ok=True)
    command = [
        "git",
        "-c",
        "user.email=connexto-workflow@localhost",
        "-c",
        "user.name=Connexto Workflow",
        *args,
    ]
    completed = subprocess.run(command, cwd=repo, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        raise AssertionError(completed.stderr)


if __name__ == "__main__":
    unittest.main()
