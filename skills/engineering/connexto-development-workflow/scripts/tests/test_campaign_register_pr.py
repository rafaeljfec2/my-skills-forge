"""Register an externally created pull request onto the active sprint."""

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
    register_existing_pull_request,
)
from connexto_workflow.errors import PolicyError


class RegisterPullRequestTests(unittest.TestCase):
    def test_registers_merged_pr_and_enables_reassociate(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            repo, gh_bin, head, merge_sha = _landed_merge(root)
            state = load_campaign(repo, "cadimlang-v1.0")
            # Simulate plan/slug mismatch vs the real PR head branch.
            state["sprints"][0]["branch"] = "feat/cad-000-wrong-slug"
            state["sprints"][0]["pr_number"] = None
            state["sprints"][0]["pr_url"] = None
            _write_state(repo, state)
            _write_pr(
                root,
                head=head,
                merge_sha=merge_sha,
                state="MERGED",
                head_ref="feat/cad-000-foundation",
                url="https://example.test/pull/48",
            )
            registered = register_existing_pull_request(
                repo,
                "cadimlang-v1.0",
                sprint="000",
                pull_request=48,
                gh_bin=gh_bin,
            )
            sprint = registered["sprints"][0]
            self.assertEqual(sprint["pr_number"], 48)
            self.assertEqual(sprint["pr_url"], "https://example.test/pull/48")
            self.assertEqual(sprint["branch"], "feat/cad-000-foundation")
            self.assertEqual(sprint["status"], "active")
            self.assertEqual(registered["current_sprint"], "000")
            self.assertIsNone(sprint["head_sha"])
            self.assertIsNone(sprint["merge_sha"])
            self.assertEqual(registered["sprints"][1]["status"], "pending")

            updated = reassociate_merged_head(
                repo,
                "cadimlang-v1.0",
                sprint="000",
                pull_request=48,
                head_sha=head,
                merge_sha=merge_sha,
                gh_bin=gh_bin,
            )
            self.assertEqual(updated["sprints"][0]["status"], "merged")
            self.assertIsNone(updated["current_sprint"])
            report = reconcile(repo, "cadimlang-v1.0", gh_bin=gh_bin)
            self.assertTrue(report["sprints"][0]["merge_on_integration"])
            self.assertEqual(report["sprints"][1]["status"], "pending")

    def test_idempotent_for_same_pr(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            repo, gh_bin, head, merge_sha = _landed_merge(root)
            _write_pr(
                root,
                head=head,
                merge_sha=merge_sha,
                state="OPEN",
                head_ref="feat/cad-000-foundation",
                url="https://example.test/pull/48",
            )
            first = register_existing_pull_request(
                repo,
                "cadimlang-v1.0",
                sprint="000",
                pull_request=48,
                gh_bin=gh_bin,
            )
            second = register_existing_pull_request(
                repo,
                "cadimlang-v1.0",
                sprint="000",
                pull_request=48,
                gh_bin=gh_bin,
            )
            self.assertEqual(first["sprints"][0]["pr_number"], 48)
            self.assertEqual(second["sprints"][0]["pr_number"], 48)
            self.assertEqual(second["current_sprint"], "000")

    def test_rejects_mismatched_existing_pr_number(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            repo, gh_bin, head, merge_sha = _landed_merge(root)
            state = load_campaign(repo, "cadimlang-v1.0")
            state["sprints"][0]["pr_number"] = 99
            _write_state(repo, state)
            _write_pr(
                root,
                head=head,
                merge_sha=merge_sha,
                state="MERGED",
                head_ref="feat/cad-000-foundation",
                url="https://example.test/pull/48",
            )
            with self.assertRaises(PolicyError):
                register_existing_pull_request(
                    repo,
                    "cadimlang-v1.0",
                    sprint="000",
                    pull_request=48,
                    gh_bin=gh_bin,
                )
            kept = load_campaign(repo, "cadimlang-v1.0")
            self.assertEqual(kept["sprints"][0]["pr_number"], 99)


def _landed_merge(root: Path) -> tuple[Path, str, str, str]:
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
    return repo, gh_bin, head, merge_sha


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


def _write_pr(
    root: Path,
    *,
    head: str,
    merge_sha: str,
    state: str,
    head_ref: str,
    url: str,
) -> None:
    (root / "pr.json").write_text(
        json.dumps(
            {
                "state": state,
                "baseRefName": "pilot-develop",
                "headRefOid": head,
                "headRefName": head_ref,
                "mergeCommit": {"oid": merge_sha},
                "statusCheckRollup": [{"conclusion": "SUCCESS"}],
                "url": url,
            }
        ),
        encoding="utf-8",
    )


def _write_state(repo: Path, state: dict[str, object]) -> None:
    path = repo / ".connexto" / "campaigns" / "cadimlang-v1.0" / "state.json"
    path.write_text(json.dumps(state), encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
