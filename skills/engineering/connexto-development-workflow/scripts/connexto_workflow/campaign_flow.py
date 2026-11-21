"""Campaign branch, review, and pull-request operations."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

from connexto_workflow.campaign_store import (
    _current,
    _git,
    _names,
    _remote_contains_sprint,
    _rev_parse,
    _save,
    _sprint_list,
    load_campaign,
)
from connexto_workflow.engine_support import refuse_commit_path
from connexto_workflow.errors import ConfigError, PolicyError, WorkflowError
from connexto_workflow.model import BLOCKING_SEVERITIES
from connexto_workflow.redact import redact


def campaign_commit(
    repo: Path,
    campaign_id: str,
    *,
    message: str,
    paths: list[str],
) -> dict[str, object]:
    state = load_campaign(repo, campaign_id)
    current = _current_branch(repo)
    refused = {
        str(state["integration_branch"]),
        str(state["release_branch"]),
        *_names(state, "protected_branches"),
    }
    if current in refused:
        raise PolicyError(f"refusing commit on {current}")
    if not message.strip() or not paths:
        raise ConfigError("commit message and paths are required")
    sprint = _current(state)
    if current != sprint["branch"]:
        raise PolicyError("commit must be on the active sprint branch")
    for rel in paths:
        refuse_commit_path(repo, rel)
    add = _git(repo, ["add", "--", *paths])
    if add.returncode != 0:
        raise WorkflowError(redact(add.stderr.strip()) or "git add failed")
    commit = _commit(repo, message.strip())
    if commit.returncode != 0:
        raise WorkflowError(redact(commit.stderr.strip()) or "git commit failed")
    sprint["head_sha"] = _rev_parse(repo, "HEAD")
    _save(repo, state)
    return state


def open_pull_request(
    repo: Path,
    campaign_id: str,
    *,
    title: str,
    body: str,
    gh_bin: str,
) -> dict[str, object]:
    state = load_campaign(repo, campaign_id)
    sprint = _current(state)
    _require_review(repo, state, sprint, "pre-pr")
    branch = str(sprint["branch"])
    integration = str(state["integration_branch"])
    pushed = _git(repo, ["push", "origin", f"HEAD:refs/heads/{branch}"])
    if pushed.returncode != 0:
        raise WorkflowError(redact(pushed.stderr.strip()) or "git push failed")
    created = _gh(
        repo,
        gh_bin,
        ["pr", "create", "--base", integration, "--head", branch, "--title", title, "--body", body],
    )
    if created.returncode != 0:
        raise WorkflowError(redact(created.stderr.strip()) or "gh pr create failed")
    url = created.stdout.strip().splitlines()[-1]
    sprint["pr_url"] = url
    sprint["pr_number"] = _pull_number(url)
    _save(repo, state)
    return state


def merge_pull_request(repo: Path, campaign_id: str, *, gh_bin: str) -> dict[str, object]:
    state = load_campaign(repo, campaign_id)
    sprint = _current(state)
    _require_review(repo, state, sprint, "pre-pr")
    _require_review(repo, state, sprint, "post-pr")
    _require_distinct_reviewers(sprint)
    before = _protected_tips(repo, state)
    number = sprint.get("pr_number")
    if not isinstance(number, int):
        raise PolicyError("pull request number is missing")
    viewed = _gh(
        repo,
        gh_bin,
        [
            "pr",
            "view",
            str(number),
            "--json",
            "state,mergeCommit,headRefOid,baseRefName,statusCheckRollup,url",
        ],
    )
    if viewed.returncode != 0:
        raise WorkflowError(redact(viewed.stderr.strip()) or "gh pr view failed")
    payload = json.loads(viewed.stdout)
    if not isinstance(payload, dict):
        raise PolicyError("pull request view is missing")
    if _checks_block(payload):
        raise PolicyError("pull request checks are not green")
    _require_reviewed_pull_request(repo, state, sprint, payload)
    remote_before = _remote_protected_tips(repo, state)
    merged = _gh(repo, gh_bin, ["pr", "merge", str(number), "--merge"])
    if merged.returncode != 0:
        raise WorkflowError(redact(merged.stderr.strip()) or "gh pr merge failed")
    _git(repo, ["fetch", "origin"])
    _require_unchanged(repo, state, before)
    _require_remote_protected(repo, remote_before)
    if not _remote_contains_sprint(repo, state, sprint):
        raise PolicyError("merge did not land on the integration branch")
    integration = str(state["integration_branch"])
    sprint["merge_sha"] = _rev_parse(repo, f"origin/{integration}")
    sprint["merge_on_integration"] = True
    sprint["status"] = "merged"
    state["current_sprint"] = None
    _save(repo, state)
    return state


def reconcile(repo: Path, campaign_id: str, *, gh_bin: str | None = None) -> dict[str, object]:
    _git(repo, ["fetch", "origin"])
    state = load_campaign(repo, campaign_id)
    for sprint in _sprint_list(state):
        sprint["merge_on_integration"] = _remote_contains_sprint(repo, state, sprint)
        number = sprint.get("pr_number")
        if gh_bin and isinstance(number, int):
            viewed = _gh(
                repo,
                gh_bin,
                [
                    "pr",
                    "view",
                    str(number),
                    "--json",
                    "state,mergeCommit,headRefOid,baseRefName,statusCheckRollup,url",
                ],
            )
            if viewed.returncode != 0:
                raise WorkflowError(redact(viewed.stderr.strip()) or "gh pr view failed")
            payload = json.loads(viewed.stdout)
            if isinstance(payload, dict):
                sprint["remote_pr"] = payload
    _save(repo, state)
    return state


def _require_review(
    repo: Path,
    state: dict[str, object],
    sprint: dict[str, object],
    stage: str,
) -> None:
    reviews = sprint["reviews"]
    if not isinstance(reviews, dict):
        raise PolicyError("sprint reviews are missing")
    review = reviews.get(stage)
    head = _rev_parse(repo, "HEAD")
    if not isinstance(review, dict):
        raise PolicyError(f"{stage} review is missing")
    if review.get("verdict") != "APPROVED":
        raise PolicyError(f"{stage} review is not APPROVED")
    if review.get("head_sha") != head:
        raise PolicyError(f"{stage} review does not match HEAD")
    risk = _risk_for(repo, str(sprint["demand_id"]))
    findings = review.get("findings")
    if not isinstance(findings, list):
        findings = []
    blocking = BLOCKING_SEVERITIES[risk]
    if any(isinstance(item, dict) and item.get("severity") in blocking for item in findings):
        raise PolicyError(f"{stage} review has a blocking finding")


def _checks_block(payload: dict[str, object]) -> bool:
    rollup = payload.get("statusCheckRollup") or []
    if not isinstance(rollup, list) or not rollup:
        return False
    allowed = {"SUCCESS", "NEUTRAL", "SKIPPED"}
    for item in rollup:
        if not isinstance(item, dict):
            return True
        conclusion = item.get("conclusion") or item.get("state")
        if conclusion not in allowed:
            return True
    return False


def _require_reviewed_pull_request(
    repo: Path,
    state: dict[str, object],
    sprint: dict[str, object],
    payload: dict[str, object],
) -> None:
    integration = str(state["integration_branch"])
    if payload.get("baseRefName") != integration:
        raise PolicyError("pull request base is not the integration branch")
    head = _rev_parse(repo, "HEAD")
    if payload.get("headRefOid") != head:
        raise PolicyError("pull request head does not match HEAD")
    reviews = sprint.get("reviews")
    if not isinstance(reviews, dict):
        raise PolicyError("sprint reviews are missing")
    for stage in ("pre-pr", "post-pr"):
        review = reviews.get(stage)
        if not isinstance(review, dict) or review.get("head_sha") != head:
            raise PolicyError(f"{stage} review does not match HEAD")


def _remote_protected_tips(repo: Path, state: dict[str, object]) -> dict[str, str]:
    names = list(dict.fromkeys([*_names(state, "protected_branches"), str(state["release_branch"])]))
    return {name: _rev_parse(repo, f"origin/{name}") for name in names}


def _require_remote_protected(repo: Path, before: dict[str, str]) -> None:
    for name, sha in before.items():
        if _rev_parse(repo, f"origin/{name}") != sha:
            raise PolicyError(f"protected branch moved: {name}")


def _require_distinct_reviewers(sprint: dict[str, object]) -> None:
    reviews = sprint["reviews"]
    if not isinstance(reviews, dict):
        raise PolicyError("sprint reviews are missing")
    pre = reviews.get("pre-pr")
    post = reviews.get("post-pr")
    if not isinstance(pre, dict) or not isinstance(post, dict):
        raise PolicyError("both reviews are required")
    if pre.get("actor_id") == post.get("actor_id") or pre.get("session_id") == post.get("session_id"):
        raise PolicyError("post-PR review must use a different actor and session")


def _risk_for(repo: Path, demand_id: str) -> str:
    path = repo / ".connexto" / "runs" / demand_id / "state.json"
    if not path.is_file():
        return "MEDIUM"
    data = json.loads(path.read_text(encoding="utf-8"))
    risk = data.get("risk") if isinstance(data, dict) else None
    if risk not in BLOCKING_SEVERITIES:
        return "MEDIUM"
    return str(risk)


def _protected_tips(repo: Path, state: dict[str, object]) -> dict[str, str]:
    return {name: _rev_parse(repo, f"refs/heads/{name}") for name in _names(state, "protected_branches")}


def _require_unchanged(repo: Path, state: dict[str, object], before: dict[str, str]) -> None:
    stored = state.get("protected_shas")
    if not isinstance(stored, dict):
        raise WorkflowError("protected SHAs are missing")
    for name, sha in before.items():
        if _rev_parse(repo, f"refs/heads/{name}") != sha or stored.get(name) != sha:
            raise PolicyError(f"protected branch moved: {name}")


def _pull_number(url: str) -> int:
    match = re.search(r"/pull/(\d+)\s*$", url)
    if match is None:
        raise WorkflowError("pull request URL has no number")
    return int(match.group(1))


def _current_branch(repo: Path) -> str:
    proc = _git(repo, ["branch", "--show-current"])
    if proc.returncode != 0 or not proc.stdout.strip():
        raise WorkflowError(redact(proc.stderr.strip()) or "git branch failed")
    return proc.stdout.strip()


def _commit(repo: Path, message: str) -> subprocess.CompletedProcess[str]:
    email = _git(repo, ["config", "--get", "user.email"])
    prefix: list[str] = []
    if email.returncode != 0 or not email.stdout.strip():
        prefix = ["-c", "user.email=connexto-workflow@localhost", "-c", "user.name=Connexto Workflow"]
    return _git(repo, [*prefix, "commit", "-m", message])


def _gh(repo: Path, binary: str, args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run([binary, *args], cwd=repo, capture_output=True, text=True, check=False)
