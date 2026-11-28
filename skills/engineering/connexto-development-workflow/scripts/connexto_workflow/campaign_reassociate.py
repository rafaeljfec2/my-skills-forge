"""Rebind an active sprint head after a merge that the checkpoint missed."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

from connexto_workflow.campaign_store import (
    _git,
    _is_ancestor,
    _save,
    _sprint,
    load_campaign,
)
from connexto_workflow.errors import PolicyError, WorkflowError
from connexto_workflow.redact import redact

_SHA = re.compile(r"^[0-9a-f]{40}$")
_ALLOWED_CHECKS = {"SUCCESS", "NEUTRAL", "SKIPPED"}


def reassociate_merged_head(
    repo: Path,
    campaign_id: str,
    *,
    sprint: str,
    pull_request: int,
    head_sha: str,
    merge_sha: str,
    gh_bin: str,
) -> dict[str, object]:
    """Point the active sprint at a merged PR head. Does not merge or open the next sprint."""
    _require_sha(head_sha, "head")
    _require_sha(merge_sha, "merge")
    _git(repo, ["fetch", "origin"])
    state = load_campaign(repo, campaign_id)
    if state.get("current_sprint") != sprint:
        raise PolicyError("reassociation applies only to the active sprint")
    current = _sprint(state, sprint)
    if current.get("pr_number") != pull_request:
        raise PolicyError("pull request number does not match the checkpoint")
    payload = _view_pull_request(repo, gh_bin, pull_request)
    if payload.get("state") != "MERGED":
        raise PolicyError("pull request is not merged")
    if payload.get("baseRefName") != state.get("integration_branch"):
        raise PolicyError("pull request base is not the integration branch")
    if payload.get("headRefOid") != head_sha:
        raise PolicyError("pull request head does not match the requested head")
    merge_commit = payload.get("mergeCommit")
    observed_merge = merge_commit.get("oid") if isinstance(merge_commit, dict) else None
    if observed_merge != merge_sha:
        raise PolicyError("pull request merge commit does not match the requested merge")
    _require_green(payload)
    branch = current.get("branch")
    if not isinstance(branch, str):
        raise PolicyError("sprint branch is missing")
    remote_head = _git(repo, ["rev-parse", "--verify", "--quiet", f"origin/{branch}"])
    if remote_head.returncode != 0 or remote_head.stdout.strip() != head_sha:
        raise PolicyError("origin branch tip does not match the requested head")
    integration = f"origin/{state['integration_branch']}"
    if not _is_ancestor(repo, head_sha, merge_sha):
        raise PolicyError("requested head is not contained in the merge commit")
    if not _is_ancestor(repo, merge_sha, integration):
        raise PolicyError("merge commit is not on the integration branch")
    current["head_sha"] = head_sha
    current["merge_sha"] = merge_sha
    current["status"] = "merged"
    if state.get("current_sprint") == sprint:
        state["current_sprint"] = None
    _save(repo, state)
    return state


def _require_sha(value: str, label: str) -> None:
    if _SHA.fullmatch(value) is None:
        raise PolicyError(f"{label} sha must be 40 lowercase hex characters")


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
            "state,mergeCommit,headRefOid,baseRefName,statusCheckRollup,url",
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
