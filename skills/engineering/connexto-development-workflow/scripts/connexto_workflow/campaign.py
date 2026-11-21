"""Sequential campaign checkpoint. One sprint is open, and the next waits on the remote."""

from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from connexto_workflow.errors import ConfigError, PolicyError, WorkflowError
from connexto_workflow.model import BLOCKING_SEVERITIES
from connexto_workflow.redact import redact
from connexto_workflow.state import atomic_write

P4_SPEC_STATUS = "PROPOSED FOR IMPLEMENTATION — not yet approved"
_SPRINT_HEADING = re.compile(r"^### Sprint (\d{3}) — (.+)$", re.M)
_FEATURE_LINE = re.compile(r"^\*\*Feature:\*\* (CAD-\d{3}) · \*\*Branch:\*\* (\S+)\s*$", re.M)
_TASK_LINE = re.compile(r"^\d+\. \*\*T(\d+) —", re.M)
_PLAN_APPROVAL = {
    "source": "operator-attestation",
    "verdict": "APPROVED",
    "attested_on": "2026-11-21",
    "scope": "campaign plan only",
    "in_repo_review_transcript": False,
    "p4_spec_status": P4_SPEC_STATUS,
}


@dataclass(frozen=True)
class SprintSpec:
    number: str
    title: str
    demand_id: str
    branch: str
    tasks: list[str]


def parse_sprints(plan_text: str) -> list[SprintSpec]:
    """Return the sprint queue. Each sprint must be exactly T1 through T4."""
    matches = list(_SPRINT_HEADING.finditer(plan_text))
    if not matches:
        raise ConfigError("plan has no sprints")
    sprints: list[SprintSpec] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(plan_text)
        body = plan_text[match.start() : end]
        feature = _FEATURE_LINE.search(body)
        if feature is None:
            raise ConfigError(f"sprint {match.group(1)} is missing its feature id and branch")
        tasks = [f"T{number}" for number in _TASK_LINE.findall(body)]
        if tasks != ["T1", "T2", "T3", "T4"]:
            raise ConfigError(f"sprint {match.group(1)} must contain exactly T1, T2, T3, and T4")
        sprints.append(
            SprintSpec(
                number=match.group(1),
                title=match.group(2).strip(),
                demand_id=feature.group(1),
                branch=feature.group(2),
                tasks=tasks,
            )
        )
    return sprints


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
    if isinstance(payload, dict) and _checks_block(payload):
        raise PolicyError("pull request checks are not green")
    merged = _gh(repo, gh_bin, ["pr", "merge", str(number), "--merge"])
    if merged.returncode != 0:
        raise WorkflowError(redact(merged.stderr.strip()) or "gh pr merge failed")
    _git(repo, ["fetch", "origin"])
    _require_unchanged(repo, state, before)
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


def _pull_number(url: str) -> int:
    match = re.search(r"/pull/(\d+)\s*$", url)
    if match is None:
        raise WorkflowError("pull request URL has no number")
    return int(match.group(1))


def _is_ancestor(repo: Path, ancestor: str, descendant: str) -> bool:
    return _git(repo, ["merge-base", "--is-ancestor", ancestor, descendant]).returncode == 0


def _current_branch(repo: Path) -> str:
    proc = _git(repo, ["branch", "--show-current"])
    if proc.returncode != 0 or not proc.stdout.strip():
        raise WorkflowError(redact(proc.stderr.strip()) or "git branch failed")
    return proc.stdout.strip()


def _rev_parse(repo: Path, revision: str) -> str:
    proc = _git(repo, ["rev-parse", "--verify", revision])
    if proc.returncode != 0:
        raise WorkflowError(redact(proc.stderr.strip()) or f"git rev-parse failed for {revision}")
    return proc.stdout.strip()


def _commit(repo: Path, message: str) -> subprocess.CompletedProcess[str]:
    email = _git(repo, ["config", "--get", "user.email"])
    prefix: list[str] = []
    if email.returncode != 0 or not email.stdout.strip():
        prefix = ["-c", "user.email=connexto-workflow@localhost", "-c", "user.name=Connexto Workflow"]
    return _git(repo, [*prefix, "commit", "-m", message])


def _git(repo: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, check=False)


def _gh(repo: Path, binary: str, args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run([binary, *args], cwd=repo, capture_output=True, text=True, check=False)


def _state_path(repo: Path, campaign_id: str) -> Path:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,80}", campaign_id):
        raise PolicyError("campaign id is invalid")
    return repo / ".connexto" / "campaigns" / campaign_id / "state.json"


def _save(repo: Path, state: dict[str, object]) -> None:
    campaign_id = state.get("campaign_id")
    if not isinstance(campaign_id, str):
        raise WorkflowError("campaign id is missing")
    atomic_write(_state_path(repo, campaign_id), json.dumps(state, indent=2, ensure_ascii=False) + "\n")
