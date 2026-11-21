"""Fixtures for the campaign controller tests."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))

import support
from connexto_workflow.campaign import (
    campaign_commit,
    init_campaign,
    open_pull_request,
    open_sprint,
    record_review,
)

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
    head_oid = subprocess.check_output(["git", "rev-parse", payload["head"]], text=True).strip()
    override = repo / ".git" / "head-override"
    if override.is_file():
        head_oid = override.read_text(encoding="utf-8").strip()
    print(json.dumps({
        "state": payload["state"],
        "mergeCommit": {"oid": payload["mergeCommit"]} if payload["mergeCommit"] else None,
        "headRefOid": head_oid,
        "baseRefName": payload["base"],
        "statusCheckRollup": payload["statusCheckRollup"],
        "url": payload["url"],
    }))
elif args[:2] == ["pr", "merge"]:
    (repo / ".git" / "merge-invoked").write_text("yes", encoding="utf-8")
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


def _ready_to_merge(root: Path) -> tuple[Path, str]:
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
    open_sprint(repo, "cadimlang-v1.0", "000")
    (repo / "pilot.txt").write_text("pilot\n", encoding="utf-8")
    campaign_commit(repo, "cadimlang-v1.0", message="test: disposable pilot note", paths=["pilot.txt"])
    record_review(
        repo,
        "cadimlang-v1.0",
        stage="pre-pr",
        verdict="APPROVED",
        actor_id="judge-pre",
        session_id="session-pre",
        findings=[],
    )
    open_pull_request(repo, "cadimlang-v1.0", title="pilot", body="pilot", gh_bin=gh_bin)
    record_review(
        repo,
        "cadimlang-v1.0",
        stage="post-pr",
        verdict="APPROVED",
        actor_id="judge-post",
        session_id="session-post",
        findings=[],
    )
    return repo, gh_bin
