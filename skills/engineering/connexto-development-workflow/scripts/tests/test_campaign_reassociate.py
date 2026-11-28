"""Recovery of a stale sprint head after an already merged pull request."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from campaign_fixture import PLAN, _git, _init_remote_repo
from connexto_workflow.campaign import (
    init_campaign,
    load_campaign,
    open_sprint,
    reassociate_merged_head,
    reconcile,
)
from connexto_workflow.errors import PolicyError


class ReassociateHeadTests(unittest.TestCase):
    def test_stale_head_is_rebound_without_opening_the_next_sprint(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            repo, gh_bin, head, merge_sha, stale = _landed_merge(root)
            state = load_campaign(repo, "cadimlang-v1.0")
            state["sprints"][0]["head_sha"] = stale
            state["sprints"][0]["pr_number"] = 48
            _write_state(repo, state)
            _write_pr(root, head, merge_sha)
            updated = reassociate_merged_head(
                repo,
                "cadimlang-v1.0",
                sprint="000",
                pull_request=48,
                head_sha=head,
                merge_sha=merge_sha,
                gh_bin=gh_bin,
            )
            sprint = updated["sprints"][0]
            self.assertEqual(sprint["head_sha"], head)
            self.assertEqual(sprint["merge_sha"], merge_sha)
            self.assertEqual(sprint["status"], "merged")
            self.assertIsNone(updated["current_sprint"])
            self.assertEqual(updated["sprints"][1]["status"], "pending")
            report = reconcile(repo, "cadimlang-v1.0", gh_bin=gh_bin)
            self.assertTrue(report["sprints"][0]["merge_on_integration"])
            self.assertIsNone(report["current_sprint"])

    def test_wrong_head_does_not_change_the_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            repo, gh_bin, head, merge_sha, stale = _landed_merge(root)
            state = load_campaign(repo, "cadimlang-v1.0")
            state["sprints"][0]["head_sha"] = stale
            state["sprints"][0]["pr_number"] = 48
            _write_state(repo, state)
            _write_pr(root, head, merge_sha)
            with self.assertRaises(PolicyError):
                reassociate_merged_head(
                    repo,
                    "cadimlang-v1.0",
                    sprint="000",
                    pull_request=48,
                    head_sha="a" * 40,
                    merge_sha=merge_sha,
                    gh_bin=gh_bin,
                )
            kept = load_campaign(repo, "cadimlang-v1.0")
            self.assertEqual(kept["sprints"][0]["head_sha"], stale)
            self.assertEqual(kept["current_sprint"], "000")


def _landed_merge(root: Path) -> tuple[Path, str, str, str, str]:
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
    stale = _git(repo, "rev-parse", "HEAD")
    (repo / "note.txt").write_text("landed\n", encoding="utf-8")
    _git(repo, "add", "note.txt")
    _git(repo, "commit", "-m", "feature")
    head = _git(repo, "rev-parse", "HEAD")
    _git(repo, "push", "origin", "HEAD:feat/cad-000-foundation")
    _git(repo, "checkout", "pilot-develop")
    _git(repo, "merge", "--no-ff", head, "-m", "merge feature")
    merge_sha = _git(repo, "rev-parse", "HEAD")
    _git(repo, "push", "origin", "pilot-develop")
    gh_bin = _viewer(root)
    return repo, gh_bin, head, merge_sha, stale


def _viewer(root: Path) -> str:
    path = root / "fake_gh.py"
    path.write_text(
        """#!/usr/bin/env python3
import json
import sys
from pathlib import Path

if sys.argv[1:3] != ["pr", "view"]:
    sys.exit(1)
print(Path(__file__).with_name("pr.json").read_text(encoding="utf-8"))
""",
        encoding="utf-8",
    )
    path.chmod(0o755)
    return str(path)


def _write_pr(root: Path, head: str, merge_sha: str) -> None:
    (root / "pr.json").write_text(
        json.dumps(
            {
                "state": "MERGED",
                "baseRefName": "pilot-develop",
                "headRefOid": head,
                "mergeCommit": {"oid": merge_sha},
                "statusCheckRollup": [{"conclusion": "SUCCESS"}],
            }
        ),
        encoding="utf-8",
    )


def _write_state(repo: Path, state: dict[str, object]) -> None:
    path = repo / ".connexto" / "campaigns" / "cadimlang-v1.0" / "state.json"
    path.write_text(json.dumps(state), encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
