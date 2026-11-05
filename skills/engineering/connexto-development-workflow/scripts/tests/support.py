"""Shared fixtures for workflow tests."""

from __future__ import annotations

import json
import shlex
import sys
from connexto_workflow.workflow_defaults import default_workflow
from pathlib import Path

from connexto_workflow.engine import Brief, Engine

PASSING_TEST = """import unittest


class OkTests(unittest.TestCase):
    def test_ok(self) -> None:
        self.assertTrue(True)


if __name__ == "__main__":
    unittest.main()
"""


def project_config(
    test_command: str,
    *,
    implement: str | None = None,
    max_attempts: int = 3,
    memory_enabled: bool = True,
    isolated: bool = False,
    allow_commit: bool = False,
    language: str | None = "python",
    framework: str | None = None,
) -> dict[str, object]:
    return {
        "project": {"name": "sample", "language": language, "framework": framework},
        "commands": {
            "install": None,
            "test": test_command,
            "lint": None,
            "typecheck": None,
            "build": None,
            "implement": implement,
        },
        "quality": {
            "require_tests": True,
            "require_lint": False,
            "require_typecheck": False,
            "require_build": False,
            "max_validate_attempts": max_attempts,
            "command_timeout_seconds": 30,
        },
        "git": {"base_branch": "main", "isolated_branch": isolated, "allow_commit": allow_commit},
        "memory": {
            "enabled": memory_enabled,
            "workspace": "default" if memory_enabled else None,
            "project": "sample" if memory_enabled else None,
        },
        "workflow": default_workflow(),
    }


def write_config(repo: Path, payload: dict[str, object]) -> None:
    (repo / "connexto.project.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def passing_command() -> str:
    return shlex.join([sys.executable, "-m", "unittest", "test_ok"])


def seed_passing(repo: Path, **overrides: object) -> None:
    repo.mkdir(parents=True, exist_ok=True)
    (repo / "test_ok.py").write_text(PASSING_TEST, encoding="utf-8")
    payload = project_config(passing_command())
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(payload.get(key), dict):
            nested = payload[key]
            if isinstance(nested, dict):
                nested.update(value)
        else:
            payload[key] = value
    write_config(repo, payload)


def brief_for(demand_id: str, demand_type: str, risk: str | None = None) -> Brief:
    return Brief(
        demand_id=demand_id,
        demand_type=demand_type,
        problem="The sample check does not record a demand.",
        desired_outcome="The demand reaches the requested state.",
        scope="test_ok.py",
        success_criteria=("the configured test command exits 0",),
        target_project="sample",
        constraints=("Stay inside the sample repository.",),
        risk=risk,
    )


def open_run(repo: Path, demand_id: str, demand_type: str, risk: str | None = None) -> Engine:
    engine = Engine(repo, demand_id)
    engine.init_run(brief_for(demand_id, demand_type, risk))
    engine.request_transition("INTAKE", "orchestrator", "orch-1", "start")
    return engine


def fill_plan(engine: Engine) -> None:
    research, spec, plan, tasks = plan_parts()
    engine.put_artifact("researcher", "res-1", "research.md", research)
    engine.request_transition("RESEARCH", "orchestrator", "orch-1", "intake_complete")
    engine.request_transition("PLAN", "researcher", "res-1", "research_complete")
    engine.put_artifact("planner", "plan-1", "spec.md", spec)
    engine.put_artifact("planner", "plan-1", "plan.md", plan)
    engine.put_artifact("planner", "plan-1", "tasks.md", tasks)
    engine.request_transition("IMPLEMENT", "planner", "plan-1", "plan_accepted")


def plan_parts() -> tuple[str, str, str, str]:
    return (
        (
            "# Research\n\n## Facts\ntest_ok.py asserts True.\n\n"
            "## Hypotheses\nThe command is the project test gate.\n\n"
            "## Gaps\nNo other packages were inspected.\n\n"
            "## Evidence\ntest_ok.py\n\nImplemented: no\n"
        ),
        "# Spec\n\n## Behavior\nThe sample test stays green.\n",
        "# Plan\n\n## Acceptance criteria\n- The configured test exits 0.\n",
        "# Tasks\n\n- [ ] Run the configured test.\n",
    )


def reach_review(engine: Engine) -> Engine:
    fill_plan(engine)
    submit_sample_report(engine, "dev-1", "dev-session-1")
    engine.run_validation("developer", "dev-1")
    return engine


def submit_sample_report(engine: Engine, actor: str, session: str) -> None:
    engine.materialize_developer_task("developer", actor, session)
    engine.submit_developer_report(
        "developer",
        actor,
        {
            "report_version": 1,
            "summary": "Sample change ready for validation.",
            "files_changed": [],
            "tests_touched": ["test_ok.py"],
            "commands_run": [{"name": "manual", "exit_code": 0}],
            "results": ["Prepared the sample tree for validation."],
            "issues": [],
            "pending": [],
            "evidence_refs": [f".connexto/runs/{engine.demand_id}/developer/task.json"],
            "developer_session_id": session,
        },
        session,
    )
    engine.note_implementation("developer", actor, "Request validation of the sample test.")
