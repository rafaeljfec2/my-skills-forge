"""Campaign pull-request and merge gates."""

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
from campaign_fixture import P4_STATUS, PLAN, _fake_gh, _git, _init_remote_repo, _ready_to_merge
from connexto_workflow.engine import Engine
from connexto_workflow.campaign import (
    campaign_commit,
    init_campaign,
    load_campaign,
    merge_pull_request,
    open_pull_request,
    open_sprint,
    record_review,
    reconcile,
)
from connexto_workflow.errors import PolicyError

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
            self.assertEqual(_git(repo, "rev-parse", "origin/main"), main_before)
            self.assertEqual(_git(repo, "rev-parse", "origin/develop"), develop_before)

    def test_merge_refuses_a_pull_request_whose_base_is_main(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            repo, gh_bin = _ready_to_merge(root)
            store = repo / ".git" / "fake-pr.json"
            payload = json.loads(store.read_text(encoding="utf-8"))
            payload["base"] = "main"
            store.write_text(json.dumps(payload), encoding="utf-8")
            origin_main = _git(repo, "rev-parse", "origin/main")
            origin_pilot = _git(repo, "rev-parse", "origin/pilot-develop")
            with self.assertRaises(PolicyError):
                merge_pull_request(repo, "cadimlang-v1.0", gh_bin=gh_bin)
            self.assertFalse((repo / ".git" / "merge-invoked").exists())
            self.assertEqual(_git(repo, "rev-parse", "origin/main"), origin_main)
            self.assertEqual(_git(repo, "rev-parse", "origin/pilot-develop"), origin_pilot)

    def test_merge_refuses_a_head_that_was_not_reviewed(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            repo, gh_bin = _ready_to_merge(root)
            (repo / ".git" / "head-override").write_text(
                "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\n",
                encoding="utf-8",
            )
            origin_pilot = _git(repo, "rev-parse", "origin/pilot-develop")
            with self.assertRaises(PolicyError):
                merge_pull_request(repo, "cadimlang-v1.0", gh_bin=gh_bin)
            self.assertFalse((repo / ".git" / "merge-invoked").exists())
            self.assertEqual(_git(repo, "rev-parse", "origin/pilot-develop"), origin_pilot)

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


if __name__ == "__main__":
    unittest.main()
