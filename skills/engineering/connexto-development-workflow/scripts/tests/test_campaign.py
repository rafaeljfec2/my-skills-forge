"""Campaign controller gates."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import support
from campaign_fixture import PLAN, SHORT_PLAN, _commit_all, _git, _init_remote_repo
from connexto_workflow.campaign import campaign_commit, init_campaign, open_sprint, parse_sprints
from connexto_workflow.commands import run_command
from connexto_workflow.engine import Engine
from connexto_workflow.engine_support import default_work_branch
from connexto_workflow.errors import ConfigError, PolicyError

class ParseTests(unittest.TestCase):
    def test_rejects_a_sprint_that_does_not_have_four_tasks(self) -> None:
        with self.assertRaises(ConfigError):
            parse_sprints(SHORT_PLAN)

    def test_reads_two_sprints_of_four_tasks(self) -> None:
        sprints = parse_sprints(PLAN)
        self.assertEqual([item.number for item in sprints], ["000", "001"])
        self.assertEqual(sprints[0].tasks, ["T1", "T2", "T3", "T4"])
        self.assertEqual(sprints[0].demand_id, "CAD-000")
        self.assertEqual(sprints[0].branch, "feat/cad-000-foundation")

    def test_rejects_a_connexto_branch_prefix(self) -> None:
        plan = PLAN.replace("feat/cad-000-foundation", "connexto/CAD-000", 1)
        with self.assertRaises(ConfigError):
            parse_sprints(plan)


class FeatureRiskTests(unittest.TestCase):
    def test_cad_feature_omitted_risk_is_medium_and_intake_does_not_wait(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            repo = Path(raw)
            support.seed_passing(repo)
            engine = Engine(repo, "CAD-000")
            engine.init_run(support.brief_for("CAD-000", "FEATURE"))
            self.assertEqual(engine.ensure().risk, "MEDIUM")
            self.assertEqual(engine.ensure().demand_type, "FEATURE")
            engine.request_transition("INTAKE", "orchestrator", "orch-1", "start")
            engine.request_transition("RESEARCH", "orchestrator", "orch-1", "intake_complete")
            self.assertEqual(engine.ensure().status, "RESEARCH")

    def test_low_risk_is_refused_for_a_feature(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            repo = Path(raw)
            support.seed_passing(repo)
            engine = Engine(repo, "CAD-000")
            with self.assertRaises(PolicyError):
                engine.init_run(support.brief_for("CAD-000", "FEATURE", "LOW"))

    def test_existing_prefixes_still_init(self) -> None:
        samples = (
            ("FEAT-001", "FEATURE"),
            ("BUG-001", "BUGFIX"),
            ("REFACTOR-001", "REFACTOR"),
            ("HOTFIX-001", "HOTFIX"),
            ("DEBT-001", "TECHNICAL_DEBT"),
        )
        with tempfile.TemporaryDirectory() as raw:
            repo = Path(raw)
            support.seed_passing(repo)
            for demand_id, demand_type in samples:
                engine = Engine(repo, demand_id)
                engine.init_run(support.brief_for(demand_id, demand_type))
                self.assertEqual(engine.ensure().demand_id, demand_id)
                self.assertEqual(
                    default_work_branch(demand_type, demand_id),
                    {
                        "FEATURE": "feat/feat-001",
                        "BUGFIX": "fix/bug-001",
                        "REFACTOR": "refactor/refactor-001",
                        "HOTFIX": "hotfix/hotfix-001",
                        "TECHNICAL_DEBT": "chore/debt-001",
                    }[demand_type],
                )
            self.assertEqual(default_work_branch("FEATURE", "CAD-000"), "feat/cad-000")




class ValidatorTests(unittest.TestCase):
    def test_validator_records_cwd_and_cannot_be_the_developer(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            repo = Path(raw)
            support.seed_passing(repo, git={"isolated_branch": False, "allow_commit": False})
            engine = support.open_run(repo, "CAD-000", "FEATURE")
            support.fill_plan(engine)
            support.submit_sample_report(engine, "dev-1", "dev-session-1")
            with self.assertRaises(PolicyError):
                engine.run_validation("validator", "dev-1")
            engine.run_validation("validator", "val-1")
            self.assertEqual(engine.ensure().status, "REVIEW")
            log = repo / ".connexto" / "runs" / "CAD-000" / "evidence" / "commands.jsonl"
            record = json.loads(log.read_text(encoding="utf-8").splitlines()[-1])
            self.assertEqual(record["cwd"], str(repo.resolve()))
            self.assertIsInstance(record["argv"], list)
            self.assertEqual(record["exit_code"], 0)
            self.assertIn("stdout_excerpt", record)

    def test_command_record_includes_the_working_directory(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            repo = Path(raw)
            log = repo / "commands.jsonl"
            command = f"{sys.executable} -c pass"
            record = run_command(repo, "noop", command, 10, log)
            self.assertEqual(record.cwd, str(repo.resolve()))


class BranchBindTests(unittest.TestCase):
    def test_bound_branch_replaces_the_connexto_prefix(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            repo = Path(raw)
            _git(repo, "init", "-b", "main")
            (repo / "README.md").write_text("base\n", encoding="utf-8")
            _commit_all(repo, "base")
            support.seed_passing(repo, git={"base_branch": "main", "isolated_branch": True, "allow_commit": False})
            engine = support.open_run(repo, "CAD-000", "FEATURE")
            research, spec, plan, tasks = support.plan_parts()
            engine.put_artifact("researcher", "res-1", "research.md", research)
            engine.request_transition("RESEARCH", "orchestrator", "orch-1", "intake_complete")
            engine.request_transition("PLAN", "researcher", "res-1", "research_complete")
            engine.put_artifact("planner", "plan-1", "spec.md", spec)
            engine.put_artifact("planner", "plan-1", "plan.md", plan)
            engine.put_artifact("planner", "plan-1", "tasks.md", tasks)
            with self.assertRaises(PolicyError):
                engine.bind_work_branch("orchestrator", "orch-1", "main")
            with self.assertRaises(PolicyError):
                engine.bind_work_branch("orchestrator", "orch-1", "connexto/CAD-000")
            engine.bind_work_branch("orchestrator", "orch-1", "docs/cad-000-notes")
            self.assertEqual(engine.ensure().git_branch, "docs/cad-000-notes")
            engine.bind_work_branch("orchestrator", "orch-1", "feat/cad-000-foundation")
            engine.request_transition("IMPLEMENT", "planner", "plan-1", "plan_accepted")
            self.assertEqual(_git(repo, "branch", "--show-current"), "feat/cad-000-foundation")
            self.assertEqual(engine.ensure().git_branch, "feat/cad-000-foundation")


class SecretPathTests(unittest.TestCase):
    def test_campaign_commit_refuses_credentials(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            repo, _bare = _init_remote_repo(root)
            init_campaign(
                repo,
                campaign_id="cadimlang-v1.0",
                plan_text=PLAN,
                integration_branch="pilot-develop",
                release_branch="main",
                protect_branches=["develop"],
            )
            open_sprint(repo, "cadimlang-v1.0", "000")
            (repo / "credentials.json").write_text("{}\n", encoding="utf-8")
            with self.assertRaises(PolicyError):
                campaign_commit(
                    repo,
                    "cadimlang-v1.0",
                    message="test: refuse a secret file",
                    paths=["credentials.json"],
                )
            self.assertNotIn("credentials.json", _git(repo, "ls-files"))


if __name__ == "__main__":
    unittest.main()
