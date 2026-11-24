"""Campaign checkpoint load and save."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

from connexto_workflow.campaign_parse import parse_sprints
from connexto_workflow.campaign_parse import _PLAN_APPROVAL
from connexto_workflow.errors import PolicyError, WorkflowError
from connexto_workflow.redact import redact
from connexto_workflow.state import atomic_write

def init_campaign(
    repo: Path,
    *,
    campaign_id: str,
    plan_text: str,
    integration_branch: str,
    release_branch: str = "main",
    protect_branches: list[str] | None = None,
) -> dict[str, object]:
    sprints = parse_sprints(plan_text)
    protected = sorted({release_branch, *(protect_branches or [])})
    if integration_branch in protected:
        raise PolicyError("the integration branch cannot also be a protected branch")
    if integration_branch == release_branch:
        raise PolicyError("the integration branch cannot be the release branch")
    state: dict[str, object] = {
        "schema_version": 1,
        "campaign_id": campaign_id,
        "integration_branch": integration_branch,
        "release_branch": release_branch,
        "protected_branches": protected,
        "protected_shas": {name: _rev_parse(repo, f"refs/heads/{name}") for name in protected},
        "status": "active",
        "current_sprint": None,
        "plan_approval": dict(_PLAN_APPROVAL),
        "sprints": [
            {
                "number": item.number,
                "title": item.title,
                "demand_id": item.demand_id,
                "branch": item.branch,
                "tasks": list(item.tasks),
                "status": "pending",
                "base_sha": None,
                "head_sha": None,
                "pr_url": None,
                "pr_number": None,
                "merge_sha": None,
                "merge_on_integration": False,
                "reviews": {"pre-pr": None, "post-pr": None},
            }
            for item in sprints
        ],
        "blockers": [],
    }
    path = _state_path(repo, campaign_id)
    if path.exists():
        raise PolicyError(f"campaign already exists: {campaign_id}")
    _save(repo, state)
    return state


def load_campaign(repo: Path, campaign_id: str) -> dict[str, object]:
    path = _state_path(repo, campaign_id)
    if not path.is_file():
        raise WorkflowError(f"no campaign state at {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("campaign_id") != campaign_id:
        raise WorkflowError("campaign state does not match the requested id")
    return data


def record_review(
    repo: Path,
    campaign_id: str,
    *,
    stage: str,
    verdict: str,
    actor_id: str,
    session_id: str,
    findings: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    if stage not in {"pre-pr", "post-pr"}:
        raise PolicyError("review stage must be pre-pr or post-pr")
    state = load_campaign(repo, campaign_id)
    sprint = _current(state)
    reviews = sprint["reviews"]
    if not isinstance(reviews, dict):
        raise WorkflowError("sprint reviews are missing")
    reviews[stage] = {
        "verdict": verdict,
        "actor_id": actor_id,
        "session_id": session_id,
        "head_sha": _rev_parse(repo, "HEAD"),
        "findings": list(findings or []),
    }
    _save(repo, state)
    return state


def _current(state: dict[str, object]) -> dict[str, object]:
    number = state.get("current_sprint")
    if not isinstance(number, str):
        raise PolicyError("no sprint is active")
    return _sprint(state, number)


def _sprint(state: dict[str, object], number: str) -> dict[str, object]:
    for sprint in _sprint_list(state):
        if sprint.get("number") == number:
            return sprint
    raise PolicyError(f"unknown sprint: {number}")


def _sprint_index(state: dict[str, object], number: str) -> int:
    for index, sprint in enumerate(_sprint_list(state)):
        if sprint.get("number") == number:
            return index
    raise PolicyError(f"unknown sprint: {number}")


def _sprint_list(state: dict[str, object]) -> list[dict[str, object]]:
    sprints = state.get("sprints")
    if not isinstance(sprints, list) or any(not isinstance(item, dict) for item in sprints):
        raise WorkflowError("campaign sprints are missing")
    return sprints


def _names(state: dict[str, object], key: str) -> list[str]:
    value = state.get(key)
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise WorkflowError(f"campaign {key} is missing")
    return value


def _rev_parse(repo: Path, revision: str) -> str:
    proc = _git(repo, ["rev-parse", "--verify", revision])
    if proc.returncode != 0:
        raise WorkflowError(redact(proc.stderr.strip()) or f"git rev-parse failed for {revision}")
    return proc.stdout.strip()


def open_sprint(repo: Path, campaign_id: str, number: str) -> dict[str, object]:
    _git(repo, ["fetch", "origin"])
    state = load_campaign(repo, campaign_id)
    sprint = _sprint(state, number)
    index = _sprint_index(state, number)
    if index > 0:
        previous = _sprint_list(state)[index - 1]
        if not _remote_contains_sprint(repo, state, previous):
            raise PolicyError("previous sprint is not merged into the integration branch")
    integration = str(state["integration_branch"])
    branch = str(sprint["branch"])
    if branch in {integration, str(state["release_branch"]), *_names(state, "protected_branches")}:
        raise PolicyError("sprint branch collides with a protected branch")
    checkout = _git(repo, ["checkout", "-B", branch, f"origin/{integration}"])
    if checkout.returncode != 0:
        raise WorkflowError(redact(checkout.stderr.strip()) or "git checkout failed")
    sprint["status"] = "active"
    sprint["base_sha"] = _rev_parse(repo, "HEAD")
    state["current_sprint"] = number
    _save(repo, state)
    return state


def _remote_contains_sprint(repo: Path, state: dict[str, object], sprint: dict[str, object]) -> bool:
    integration = f"origin/{state['integration_branch']}"
    head_sha = sprint.get("head_sha")
    branch = sprint.get("branch")
    if not isinstance(head_sha, str) or not isinstance(branch, str):
        return False
    remote_head = _git(repo, ["rev-parse", "--verify", "--quiet", f"origin/{branch}"])
    if remote_head.returncode != 0 or remote_head.stdout.strip() != head_sha:
        return False
    return _is_ancestor(repo, head_sha, integration)


def _is_ancestor(repo: Path, ancestor: str, descendant: str) -> bool:
    return _git(repo, ["merge-base", "--is-ancestor", ancestor, descendant]).returncode == 0


def _git(repo: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, check=False)


def _state_path(repo: Path, campaign_id: str) -> Path:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,80}", campaign_id):
        raise PolicyError("campaign id is invalid")
    return repo / ".connexto" / "campaigns" / campaign_id / "state.json"


def _save(repo: Path, state: dict[str, object]) -> None:
    campaign_id = state.get("campaign_id")
    if not isinstance(campaign_id, str):
        raise WorkflowError("campaign id is missing")
    atomic_write(_state_path(repo, campaign_id), json.dumps(state, indent=2, ensure_ascii=False) + "\n")
