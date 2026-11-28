"""Register an already-created pull request onto the active campaign sprint."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from connexto_workflow.campaign_store import (
    _names,
    _save,
    _sprint,
    load_campaign,
)
from connexto_workflow.errors import PolicyError, WorkflowError
from connexto_workflow.redact import redact

_ALLOWED_CHECKS = {"SUCCESS", "NEUTRAL", "SKIPPED"}


def register_existing_pull_request(
    repo: Path,
    campaign_id: str,
    *,
    sprint: str,
    pull_request: int,
    gh_bin: str,
) -> dict[str, object]:
    """Bind an existing PR to the active sprint. Does not create, merge, or close the sprint."""
    state = load_campaign(repo, campaign_id)
    if state.get("current_sprint") != sprint:
        raise PolicyError("registration applies only to the active sprint")
    current = _sprint(state, sprint)
    if current.get("status") != "active":
        raise PolicyError("sprint is not active")
    existing = current.get("pr_number")
    if isinstance(existing, int) and existing != pull_request:
        raise PolicyError("pull request number does not match the checkpoint")
    payload = _view_pull_request(repo, gh_bin, pull_request)
    state_name = payload.get("state")
    if state_name not in {"OPEN", "MERGED"}:
        raise PolicyError("pull request must be OPEN or MERGED")
    if payload.get("baseRefName") != state.get("integration_branch"):
        raise PolicyError("pull request base is not the integration branch")
    if state_name == "MERGED":
        _require_green(payload)
    head_ref = payload.get("headRefName")
    if not isinstance(head_ref, str) or not head_ref.strip():
        raise PolicyError("pull request head branch is missing")
    branch = head_ref.strip()
    refused = {
        str(state["integration_branch"]),
        str(state["release_branch"]),
        *_names(state, "protected_branches"),
    }
    if branch in refused:
        raise PolicyError("pull request head branch collides with a protected branch")
    url = payload.get("url")
    if not isinstance(url, str) or not url.strip():
        raise PolicyError("pull request URL is missing")
    # Idempotent when the same PR is already registered: refresh URL/branch only.
    current["pr_number"] = pull_request
    current["pr_url"] = url.strip()
    current["branch"] = branch
    _save(repo, state)
    return state


def _require_green(payload: dict[str, object]) -> None:
    rollup = payload.get("statusCheckRollup")
    if not isinstance(rollup, list) or not rollup:
        raise PolicyError("pull request checks are missing")
    for item in rollup:
        if not isinstance(item, dict):
            raise PolicyError("pull request checks are not green")
        conclusion = item.get("conclusion") or item.get("state")
        if conclusion not in _ALLOWED_CHECKS:
            raise PolicyError("pull request checks are not green")


def _view_pull_request(repo: Path, gh_bin: str, number: int) -> dict[str, object]:
    viewed = subprocess.run(
        [
            gh_bin,
            "pr",
            "view",
            str(number),
            "--json",
            "state,mergeCommit,headRefOid,headRefName,baseRefName,statusCheckRollup,url",
        ],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )
    if viewed.returncode != 0:
        raise WorkflowError(redact(viewed.stderr.strip()) or "gh pr view failed")
    payload = json.loads(viewed.stdout)
    if not isinstance(payload, dict):
        raise PolicyError("pull request view is missing")
    return payload
