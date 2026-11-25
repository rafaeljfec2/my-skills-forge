"""Insert plan-only sprints into an existing checkpoint without rewriting history."""

from __future__ import annotations

from pathlib import Path

from connexto_workflow.campaign_parse import SprintSpec, parse_sprints
from connexto_workflow.campaign_store import _save, load_campaign
from connexto_workflow.errors import PolicyError

_CLOSED = {"merged", "consolidated"}


def reconcile_plan(
    repo: Path,
    campaign_id: str,
    plan_text: str,
    *,
    dry_run: bool = False,
) -> dict[str, object]:
    """Align the checkpoint queue to the parsed plan. Existing sprint objects are reused."""
    parsed = parse_sprints(plan_text)
    _reject_duplicate_plan(parsed)
    state = load_campaign(repo, campaign_id)
    if state.get("schema_version") != 1:
        raise PolicyError("campaign schema_version is not 1")
    existing = _sprint_list(state)
    by_id = {str(item["demand_id"]): item for item in existing}
    plan_ids = [item.demand_id for item in parsed]
    existing_ids = [str(item["demand_id"]) for item in existing]
    if [item for item in existing_ids if item not in set(plan_ids)]:
        raise PolicyError("plan removes a checkpoint sprint")
    if [item for item in plan_ids if item in by_id] != existing_ids:
        raise PolicyError("plan reorders checkpoint sprints")
    rebuilt: list[dict[str, object]] = []
    insertions: list[dict[str, object]] = []
    for spec in parsed:
        current = by_id.get(spec.demand_id)
        if current is None:
            rebuilt.append(_pending(spec))
            continue
        _require_same_identity(current, spec)
        rebuilt.append(current)
    for index, item in enumerate(rebuilt):
        if item.get("status") != "pending" or str(item["demand_id"]) in existing_ids:
            continue
        insertions.append(
            {
                "number": item["number"],
                "demand_id": item["demand_id"],
                "after": rebuilt[index - 1]["demand_id"] if index else None,
                "before": rebuilt[index + 1]["demand_id"] if index + 1 < len(rebuilt) else None,
            }
        )
    report: dict[str, object] = {
        "dry_run": dry_run or not insertions,
        "insertions": insertions,
        "queue": [str(item["demand_id"]) for item in rebuilt],
        "next_eligible": _next_eligible(rebuilt),
    }
    if dry_run or not insertions:
        return report
    state["sprints"] = rebuilt
    _save(repo, state)
    report["dry_run"] = False
    return report


def _reject_duplicate_plan(parsed: list[SprintSpec]) -> None:
    numbers: set[str] = set()
    demands: set[str] = set()
    for item in parsed:
        if item.number in numbers or item.demand_id in demands:
            raise PolicyError("plan repeats a sprint identity")
        numbers.add(item.number)
        demands.add(item.demand_id)


def _sprint_list(state: dict[str, object]) -> list[dict[str, object]]:
    raw = state.get("sprints")
    if not isinstance(raw, list):
        raise PolicyError("campaign sprints are missing")
    sprints: list[dict[str, object]] = []
    for item in raw:
        if not isinstance(item, dict):
            raise PolicyError("campaign sprint is not an object")
        sprints.append(item)
    return sprints


def _require_same_identity(current: dict[str, object], spec: SprintSpec) -> None:
    tasks = current.get("tasks")
    if not isinstance(tasks, list):
        raise PolicyError("checkpoint tasks are missing")
    same = (
        current.get("number") == spec.number
        and current.get("title") == spec.title
        and current.get("demand_id") == spec.demand_id
        and current.get("branch") == spec.branch
        and list(tasks) == list(spec.tasks)
    )
    if not same:
        raise PolicyError(f"plan changes sprint {spec.demand_id}")


def _pending(spec: SprintSpec) -> dict[str, object]:
    return {
        "number": spec.number,
        "title": spec.title,
        "demand_id": spec.demand_id,
        "branch": spec.branch,
        "tasks": list(spec.tasks),
        "status": "pending",
        "base_sha": None,
        "head_sha": None,
        "pr_url": None,
        "pr_number": None,
        "merge_sha": None,
        "merge_on_integration": False,
        "reviews": {"pre-pr": None, "post-pr": None},
    }


def _next_eligible(sprints: list[dict[str, object]]) -> str | None:
    for item in sprints:
        if item.get("status") not in _CLOSED:
            demand = item.get("demand_id")
            return str(demand) if isinstance(demand, str) else None
    return None
