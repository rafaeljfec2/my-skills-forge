"""Campaign controller gates. These tests describe behavior the engine does not have yet."""

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
from connexto_workflow.campaign import (
    campaign_commit,
    init_campaign,
    load_campaign,
    merge_pull_request,
    open_pull_request,
    open_sprint,
    parse_sprints,
    record_review,
    reconcile,
)
from connexto_workflow.commands import run_command
from connexto_workflow.engine import Engine
from connexto_workflow.errors import ConfigError, PolicyError

P4_STATUS = "PROPOSED FOR IMPLEMENTATION — not yet approved"
PLAN = """### Sprint 000 — Foundation

**Feature:** CAD-000 · **Branch:** feat/cad-000-foundation

1. **T1 — adapter.** AC: config
2. **T2 — coordinator.** AC: state
3. **T3 — roles.** AC: actors
4. **T4 — pilot.** AC: merge

### Sprint 001 — Next

**Feature:** CAD-001 · **Branch:** feat/cad-001-next

1. **T1 — one.** AC: a
2. **T2 — two.** AC: b
3. **T3 — three.** AC: c
4. **T4 — four.** AC: d
"""
SHORT_PLAN = """### Sprint 000 — Foundation

**Feature:** CAD-000 · **Branch:** feat/cad-000-foundation

1. **T1 — adapter.** AC: config
2. **T2 — coordinator.** AC: state
3. **T3 — roles.** AC: actors
"""


def _git(repo: Path, *args: str) -> str:
    repo.mkdir(parents=True, exist_ok=True)
    completed = subprocess.run(
        [
            "git",
            "-c",
            "user.email=connexto-workflow@localhost",
            "-c",
            "user.name=Connexto Workflow",
            *args,
        ],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _commit_all(repo: Path, message: str) -> None:
    _git(repo, "add", "-A")
    _git(repo, "commit", "-m", message)


def _init_remote_repo(root: Path) -> tuple[Path, Path]:
    bare = root / "origin.git"
    repo = root / "work"
    _git(bare, "init", "--bare", "-b", "main")
    _git(repo, "init", "-b", "main")
    (repo / "README.md").write_text("base\n", encoding="utf-8")
    _commit_all(repo, "base")
    _git(repo, "branch", "develop")
    _git(repo, "branch", "pilot-develop")
    _git(repo, "remote", "add", "origin", str(bare))
    _git(repo, "push", "origin", "main", "develop", "pilot-develop")
    support.seed_passing(
        repo,
        git={"base_branch": "pilot-develop", "isolated_branch": True, "allow_commit": False},
    )
    _commit_all(repo, "adapter")
    _git(repo, "push", "origin", "main")
    return repo, bare


def _fake_gh(root: Path) -> Path:
    path = root / "fake_gh.py"
    path.write_text(
        """#!/usr/bin/env python3
import json
import subprocess
import sys
from pathlib import Path

repo = Path.cwd()
store = repo / ".git" / "fake-pr.json"
args = sys.argv[1:]


def flag(name: str) -> str:
    return args[args.index(name) + 1]


if args[:2] == ["pr", "create"]:
    payload = {
        "number": 1,
        "url": "https://example.test/pull/1",
        "state": "OPEN",
        "head": flag("--head"),
        "base": flag("--base"),
        "mergeCommit": None,
        "statusCheckRollup": [{"name": "pilot", "conclusion": "SUCCESS"}],
    }
    store.write_text(json.dumps(payload), encoding="utf-8")
    print(payload["url"])
elif args[:2] == ["pr", "view"]:
    payload = json.loads(store.read_text(encoding="utf-8"))
    print(json.dumps({
        "state": payload["state"],
        "mergeCommit": {"oid": payload["mergeCommit"]} if payload["mergeCommit"] else None,
        "headRefOid": subprocess.check_output(["git", "rev-parse", payload["head"]], text=True).strip(),
        "baseRefName": payload["base"],
        "statusCheckRollup": payload["statusCheckRollup"],
        "url": payload["url"],
    }))
elif args[:2] == ["pr", "merge"]:
    payload = json.loads(store.read_text(encoding="utf-8"))
    worktree = repo.parent / "merge-worktree"
    subprocess.check_call(["git", "fetch", "origin", payload["base"], payload["head"]])
    subprocess.check_call(["git", "worktree", "add", "--detach", str(worktree), f"origin/{payload['base']}"])
    subprocess.check_call(
        ["git", "-c", "user.email=connexto-workflow@localhost", "-c", "user.name=Connexto Workflow", "merge", "--no-ff", payload["head"], "-m", "merge disposable"],
        cwd=worktree,
    )
    subprocess.check_call(["git", "push", "origin", f"HEAD:refs/heads/{payload['base']}"], cwd=worktree)
    payload["state"] = "MERGED"
    payload["mergeCommit"] = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=worktree, text=True).strip()
    store.write_text(json.dumps(payload), encoding="utf-8")
else:
    raise SystemExit(f"unexpected gh args: {args}")
""",
        encoding="utf-8",
    )
    path.chmod(0o755)
    return path


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


class CampaignFlowTests(unittest.TestCase):
    def test_state_is_separate_and_survives_a_new_load(self) -> None:
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
            engine = Engine(repo, "CAD-000")
            engine.init_run(support.brief_for("CAD-000", "FEATURE"))
            campaign_path = repo / ".connexto" / "campaigns" / "cadimlang-v1.0" / "state.json"
            run_path = repo / ".connexto" / "runs" / "CAD-000" / "state.json"
            self.assertNotEqual(campaign_path, run_path)
            self.assertTrue(campaign_path.is_file())
            self.assertTrue(run_path.is_file())
            reloaded = load_campaign(repo, "cadimlang-v1.0")
            self.assertEqual(reloaded["campaign_id"], "cadimlang-v1.0")
            self.assertEqual(reloaded["plan_approval"]["source"], "operator-attestation")
            self.assertEqual(reloaded["plan_approval"]["verdict"], "APPROVED")
            self.assertEqual(reloaded["plan_approval"]["attested_on"], "2026-11-21")
            self.assertFalse(reloaded["plan_approval"]["in_repo_review_transcript"])
            self.assertEqual(reloaded["plan_approval"]["p4_spec_status"], P4_STATUS)
            self.assertEqual(json.loads(run_path.read_text(encoding="utf-8"))["demand_id"], "CAD-000")

    def test_local_merged_flag_does_not_open_the_next_sprint(self) -> None:
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
            state = load_campaign(repo, "cadimlang-v1.0")
            state["sprints"][0]["status"] = "merged"
            state["sprints"][0]["merge_sha"] = "deadbeefdeadbeefdeadbeefdeadbeefdeadbeef"
            campaign_path = repo / ".connexto" / "campaigns" / "cadimlang-v1.0" / "state.json"
            campaign_path.write_text(json.dumps(state), encoding="utf-8")
            with self.assertRaises(PolicyError):
                open_sprint(repo, "cadimlang-v1.0", "001")

    def test_disposable_merge_advances_and_protects_main_and_develop(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            repo, _bare = _init_remote_repo(root)
            gh_bin = str(_fake_gh(root))
            init_campaign(
                repo,
                campaign_id="cadimlang-v1.0",
                plan_text=PLAN,
                integration_branch="pilot-develop",
                release_branch="main",
                protect_branches=["develop"],
            )
            main_before = _git(repo, "rev-parse", "refs/heads/main")
            develop_before = _git(repo, "rev-parse", "refs/heads/develop")
            open_sprint(repo, "cadimlang-v1.0", "000")
            (repo / "pilot.txt").write_text("pilot\n", encoding="utf-8")
            campaign_commit(
                repo,
                "cadimlang-v1.0",
                message="test: disposable pilot note",
                paths=["pilot.txt"],
            )
            record_review(
                repo,
                "cadimlang-v1.0",
                stage="pre-pr",
                verdict="APPROVED_WITH_NOTES",
                actor_id="judge-pre",
                session_id="session-pre",
                findings=[],
            )
            with self.assertRaises(PolicyError):
                open_pull_request(
                    repo,
                    "cadimlang-v1.0",
                    title="pilot",
                    body="pilot",
                    gh_bin=gh_bin,
                )
            self.assertFalse((repo / ".git" / "fake-pr.json").exists())
            record_review(
                repo,
                "cadimlang-v1.0",
                stage="pre-pr",
                verdict="APPROVED",
                actor_id="judge-pre",
                session_id="session-pre",
                findings=[{"severity": "important", "rationale": "blocks"}],
            )
            with self.assertRaises(PolicyError):
                open_pull_request(
                    repo,
                    "cadimlang-v1.0",
                    title="pilot",
                    body="pilot",
                    gh_bin=gh_bin,
                )
            record_review(
                repo,
                "cadimlang-v1.0",
                stage="pre-pr",
                verdict="APPROVED",
                actor_id="judge-pre",
                session_id="session-pre",
                findings=[],
            )
            (repo / "pilot.txt").write_text("pilot changed\n", encoding="utf-8")
            campaign_commit(
                repo,
                "cadimlang-v1.0",
                message="test: stale the approval",
                paths=["pilot.txt"],
            )
            with self.assertRaises(PolicyError):
                open_pull_request(
                    repo,
                    "cadimlang-v1.0",
                    title="pilot",
                    body="pilot",
                    gh_bin=gh_bin,
                )
            record_review(
                repo,
                "cadimlang-v1.0",
                stage="pre-pr",
                verdict="APPROVED",
                actor_id="judge-pre",
                session_id="session-pre",
                findings=[],
            )
            opened = open_pull_request(
                repo,
                "cadimlang-v1.0",
                title="pilot",
                body="pilot",
                gh_bin=gh_bin,
            )
            self.assertEqual(opened["sprints"][0]["pr_url"], "https://example.test/pull/1")
            record_review(
                repo,
                "cadimlang-v1.0",
                stage="post-pr",
                verdict="APPROVED",
                actor_id="judge-pre",
                session_id="session-post",
                findings=[],
            )
            with self.assertRaises(PolicyError):
                merge_pull_request(repo, "cadimlang-v1.0", gh_bin=gh_bin)
            record_review(
                repo,
                "cadimlang-v1.0",
                stage="post-pr",
                verdict="APPROVED",
                actor_id="judge-post",
                session_id="session-post",
                findings=[],
            )
            merged = merge_pull_request(repo, "cadimlang-v1.0", gh_bin=gh_bin)
            report = reconcile(repo, "cadimlang-v1.0", gh_bin=gh_bin)
            remote_tip = _git(repo, "rev-parse", "origin/pilot-develop")
            self.assertEqual(merged["sprints"][0]["merge_sha"], remote_tip)
            self.assertTrue(report["sprints"][0]["merge_on_integration"])
            self.assertEqual(_git(repo, "rev-parse", "refs/heads/main"), main_before)
            self.assertEqual(_git(repo, "rev-parse", "refs/heads/develop"), develop_before)
            self.assertEqual(_git(repo, "rev-parse", "refs/heads/pilot-develop"), develop_before)
            advanced = open_sprint(repo, "cadimlang-v1.0", "001")
            self.assertEqual(advanced["current_sprint"], "001")

    def test_commit_on_develop_or_main_is_refused_and_cdw_commit_stays_closed(self) -> None:
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
            _git(repo, "checkout", "develop")
            (repo / "pilot.txt").write_text("nope\n", encoding="utf-8")
            with self.assertRaises(PolicyError):
                campaign_commit(repo, "cadimlang-v1.0", message="no", paths=["pilot.txt"])
            _git(repo, "checkout", "main")
            with self.assertRaises(PolicyError):
                campaign_commit(repo, "cadimlang-v1.0", message="no", paths=["pilot.txt"])
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "cdw.py"),
                    "commit",
                    "--repo",
                    str(repo),
                    "--run",
                    "CAD-000",
                    "--role",
                    "orchestrator",
                    "--actor",
                    "orch-1",
                    "--message",
                    "should fail",
                    "--path",
                    "README.md",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(completed.returncode, 0)


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
            engine.bind_work_branch("orchestrator", "orch-1", "feat/cad-000-foundation")
            engine.request_transition("IMPLEMENT", "planner", "plan-1", "plan_accepted")
            self.assertEqual(_git(repo, "branch", "--show-current"), "feat/cad-000-foundation")
            self.assertEqual(engine.ensure().git_branch, "feat/cad-000-foundation")


if __name__ == "__main__":
    unittest.main()
