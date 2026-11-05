"""End-to-end proof against a temporary git repository. No network and no LLM."""

from __future__ import annotations

import json
import shlex
import subprocess
import sys
from pathlib import Path

from connexto_workflow.engine import Brief, Engine
from connexto_workflow.errors import WorkflowError
from connexto_workflow.workflow_defaults import default_workflow

_BACKENDS = Path(__file__).resolve().parents[1] / "backends"


def run_proof(dest: Path) -> dict[str, object]:
    """Create a project under dest and take one feature from intake through done."""
    if dest.exists() and any(dest.iterdir()):
        raise WorkflowError(f"proof destination is not empty: {dest}")
    dest.mkdir(parents=True, exist_ok=True)
    _git(dest, "init", "-b", "main", identity=False)
    test_path = dest / "test_calc.py"
    test_path.write_text(_TEST, encoding="utf-8")
    command = shlex.join([sys.executable, "-m", "unittest", "test_calc"])
    dev_cmd = shlex.join([sys.executable, str(_BACKENDS / "dev_worker.py")])
    judge_cmd = shlex.join([sys.executable, str(_BACKENDS / "judge_worker.py")])
    (dest / "connexto.project.json").write_text(
        json.dumps(_config(command, dev_cmd, judge_cmd), indent=2) + "\n",
        encoding="utf-8",
    )
    _git(dest, "add", "test_calc.py", "connexto.project.json")
    _git(dest, "commit", "-m", "Add a failing calc test")
    observed = test_path.read_text(encoding="utf-8")
    if "sum_values" not in observed:
        raise WorkflowError("proof test file does not mention sum_values")

    engine = Engine(dest, "FEAT-001")
    engine.init_run(
        Brief(
            demand_id="FEAT-001",
            demand_type="FEATURE",
            problem="test_calc.py imports sum_values, and calc.py does not exist.",
            desired_outcome="sum_values adds the integers it receives.",
            scope="calc.py",
            success_criteria=("sum_values([1, 2]) returns 3",),
            target_project="calc-demo",
            constraints=("Do not add dependencies.",),
        )
    )
    engine.request_transition("INTAKE", "orchestrator", "orch-1", "start")
    engine.put_artifact(
        "researcher",
        "res-1",
        "research.md",
        "# Research\n\n"
        "## Facts\n"
        f"Observed test_calc.py imports sum_values. Excerpt: {observed.splitlines()[2]}\n\n"
        "## Hypotheses\ncalc.py is absent, so the configured unittest fails on import.\n\n"
        "## Gaps\nNo production module has been read because it is not in the tree.\n\n"
        "## Evidence\nFile test_calc.py in the repository root.\n\n"
        "Implemented: no\n",
    )
    engine.request_transition("RESEARCH", "orchestrator", "orch-1", "intake_complete")
    engine.request_transition("PLAN", "researcher", "res-1", "research_complete")
    engine.put_artifact(
        "planner",
        "plan-1",
        "spec.md",
        "# Spec\n\n## Behavior\nsum_values returns the arithmetic sum of a list of integers.\n",
    )
    engine.put_artifact(
        "planner",
        "plan-1",
        "plan.md",
        "# Plan\n\n## Acceptance criteria\n- python -m unittest test_calc exits 0.\n",
    )
    engine.put_artifact(
        "planner",
        "plan-1",
        "tasks.md",
        "# Tasks\n\n- [ ] Add calc.sum_values after the existing test fails.\n",
    )
    engine.request_transition("IMPLEMENT", "planner", "plan-1", "plan_accepted")
    engine.materialize_developer_task("developer", "dev-1", "dev-session-proof")
    engine.submit_developer_report(
        "developer",
        "dev-1",
        {
            "report_version": 1,
            "summary": "Baseline validation before implementing calc.py.",
            "files_changed": [],
            "tests_touched": ["test_calc.py"],
            "commands_run": [],
            "results": ["Expect the unittest to fail until calc.py exists."],
            "issues": [],
            "pending": ["Implement calc.sum_values"],
            "evidence_refs": [".connexto/runs/FEAT-001/developer/task.json"],
            "developer_session_id": "dev-session-proof",
        },
        "dev-session-proof",
    )
    engine.run_validation("developer", "dev-1")
    if engine.ensure().status != "IMPLEMENT":
        raise WorkflowError("the first validation should return to IMPLEMENT")
    engine.run_developer_backend("developer", "dev-1", "dev-session-proof")
    engine.run_validation("developer", "dev-1")
    if engine.ensure().status != "REVIEW":
        state = engine.ensure()
        raise WorkflowError(
            f"validation did not reach REVIEW; status={state.status} failures={state.failures}"
        )
    engine.commit_work("developer", "dev-1", "Add sum_values", ["calc.py"])
    engine.run_independent_judge("reviewer", "rev-1", "review-session-proof")
    if engine.ensure().status != "DELIVERY":
        raise WorkflowError("independent review did not clear delivery")
    engine.compose_delivery(
        "orchestrator",
        "orch-1",
        {
            "problem_solved": "test_calc.py can import sum_values and the sum assertion passes.",
            "solution": "calc.py defines sum_values as the arithmetic sum of its input.",
            "files_changed": "calc.py",
            "limitations": "Proof uses bundled subprocess backends, not a hosted LLM.",
            "follow_ups": "Point workflow.developer_command and judge_command at your agent runtime.",
        },
    )
    engine.request_transition("MEMORY", "orchestrator", "orch-1", "delivery_recorded")
    payload = engine.memory_payload()
    engine.ack_memory("orchestrator", "orch-1", "runs/FEAT-001.md")
    resumed = Engine(dest, "FEAT-001").load().status
    exits = [
        record.get("exit_code")
        for record in payload.get("commands", [])
        if isinstance(record, dict) and record.get("name") == "test"
    ]
    return {
        "demand_id": "FEAT-001",
        "final_status": engine.ensure().status,
        "resumed_status": resumed,
        "validate_exits": exits,
        "git_branch": engine.ensure().git_branch,
        "git_commit": engine.ensure().git_commit,
        "memory_page": engine.ensure().memory_ack_page,
        "memory_remote_status": engine.ensure().memory_remote_status,
        "developer_session_id": engine.ensure().developer_session_id,
        "reviewer_session_id": engine.ensure().reviewer_session_id,
        "payload_project": payload.get("project"),
    }


def _config(test_command: str, developer_command: str, judge_command: str) -> dict[str, object]:
    workflow = default_workflow()
    workflow["developer_command"] = developer_command
    workflow["judge_command"] = judge_command
    return {
        "project": {"name": "calc-demo", "language": "python", "framework": None},
        "commands": {
            "install": None,
            "test": test_command,
            "lint": None,
            "typecheck": None,
            "build": None,
            "implement": None,
        },
        "quality": {
            "require_tests": True,
            "require_lint": False,
            "require_typecheck": False,
            "require_build": False,
            "max_validate_attempts": 3,
            "command_timeout_seconds": 60,
        },
        "git": {"base_branch": "main", "isolated_branch": True, "allow_commit": True},
        "memory": {"enabled": True, "workspace": "default", "project": "calc-demo"},
        "workflow": workflow,
    }


def _git(repo: Path, *args: str, identity: bool = True) -> None:
    command = ["git"]
    if identity:
        command.extend(
            ["-c", "user.email=connexto-workflow@localhost", "-c", "user.name=Connexto Workflow"]
        )
    command.extend(args)
    completed = subprocess.run(command, cwd=repo, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        raise WorkflowError(completed.stderr.strip() or f"git {' '.join(args)} failed")


_TEST = """import unittest

from calc import sum_values


class CalcTests(unittest.TestCase):
    def test_sum_values(self) -> None:
        self.assertEqual(sum_values([1, 2]), 3)


if __name__ == "__main__":
    unittest.main()
"""
