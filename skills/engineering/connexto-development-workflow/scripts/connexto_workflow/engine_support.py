"""Shared types and helpers for the workflow engine."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from connexto_workflow.errors import ConfigError, PolicyError
from connexto_workflow.model import DEFAULT_RISK, DEMAND_TYPES, RISK_RANK

DEMAND_ID = re.compile(r"^[A-Z][A-Z0-9]*-\d{3,}$")
ACTOR_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,40}$")
PAGE = re.compile(r"^[A-Za-z0-9_./-]{3,200}$")
ROLES = frozenset({"orchestrator", "researcher", "planner", "developer", "reviewer"})
RESET_REASONS = frozenset(
    {
        "validation_failed",
        "review_defect",
        "review_solution_failure",
        "scope_change",
        "inconsistent_plan",
    }
)
RELEASE_KEYS = ("merge", "production_publish", "deploy")
RELEASE_CLAIM = re.compile(
    r"(?i)\b(merged to main|merged to master|published to production|deployed to production)\b"
)
SECRET_PATH_PARTS = frozenset({".connexto", ".env", ".git"})


@dataclass(frozen=True)
class Brief:
    demand_id: str
    demand_type: str
    problem: str
    desired_outcome: str
    scope: str
    success_criteria: tuple[str, ...]
    target_project: str
    constraints: tuple[str, ...] = ()
    risk: str | None = None


def effective_risk(demand_type: str, explicit: str | None) -> str:
    base = DEFAULT_RISK[demand_type]
    if explicit is None:
        return base
    if explicit not in RISK_RANK:
        raise ConfigError(f"unknown risk: {explicit}")
    if RISK_RANK[explicit] < RISK_RANK[base]:
        raise PolicyError(f"cannot lower {demand_type} risk from {base} to {explicit}")
    return explicit


def require_demand_type(demand_type: str) -> str:
    if demand_type not in DEMAND_TYPES:
        raise ConfigError(f"unknown demand type: {demand_type}")
    return demand_type


def require_demand_id(demand_id: str, demand_type: str | None) -> str:
    if not DEMAND_ID.match(demand_id):
        raise ConfigError("demand id must look like FEAT-001")
    if demand_type is not None:
        prefix = DEMAND_TYPES[demand_type]
        if not demand_id.startswith(prefix + "-"):
            raise ConfigError(f"{demand_type} ids must start with {prefix}-")
    return demand_id


def require_text(value: str, label: str) -> None:
    if not value.strip():
        raise ConfigError(f"{label} is empty")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def command_detail(name: str, exit_code: int | None) -> str:
    rendered = "timeout" if exit_code is None else str(exit_code)
    return f"{name} exit {rendered}"


def is_inside(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True
