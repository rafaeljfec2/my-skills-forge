"""Transition preconditions, apply, and approval parking."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from connexto_workflow.developer import developer_dir
from connexto_workflow.engine_support import RESET_REASONS, require_text, utc_now
from connexto_workflow.errors import InvalidTransition, PolicyError, PreconditionError
from connexto_workflow.model import EDGE_ROLES, EDGES, INTERNAL_ONLY
from connexto_workflow.redact import redact
from connexto_workflow.state import RunState

if TYPE_CHECKING:
    from connexto_workflow.engine import Engine


def check_preconditions(engine: Engine, source: str, to: str, reason: str) -> list[str]:
    state = engine.ensure()
    problems: list[str] = []
    if (source, to) == ("INTAKE", "RESEARCH"):
        brief = engine._read_optional("brief.md")
        if f"Demand: {state.demand_id}" not in brief:
            problems.append("brief.md is missing the demand id")
        for heading in ("## Problem", "## Desired outcome", "## Success criteria"):
            if heading not in brief:
                problems.append(f"brief.md is missing {heading}")
        if not (engine.run_dir / "project.snapshot.json").is_file():
            problems.append("project snapshot is missing")
    if (source, to) == ("RESEARCH", "PLAN"):
        body = engine._read_optional("research.md")
        for heading in ("## Facts", "## Hypotheses", "## Gaps", "## Evidence"):
            if heading not in body:
                problems.append(f"research.md is missing {heading}")
        if not re.search(r"(?m)^Implemented: no\s*$", body):
            problems.append("research.md must contain the line 'Implemented: no'")
    if (source, to) == ("PLAN", "IMPLEMENT") and reason == "plan_accepted":
        spec = engine._read_optional("spec.md")
        plan = engine._read_optional("plan.md")
        tasks = engine._read_optional("tasks.md")
        if "## Behavior" not in spec:
            problems.append("spec.md is missing ## Behavior")
        if "## Acceptance criteria" not in plan:
            problems.append("plan.md is missing ## Acceptance criteria")
        if "- [ ]" not in tasks:
            problems.append("tasks.md has no open task")
    if (source, to) == ("IMPLEMENT", "VALIDATE"):
        report_path = developer_dir(engine.run_dir) / "report.json"
        if not state.implementation_ready:
            problems.append("implementation is not ready")
        if not state.developer_id:
            problems.append("developer_id is not set")
        if not state.implement_hook_succeeded and not report_path.is_file():
            problems.append("developer/report.json or a successful implement hook is required")
    if (source, to) == ("VALIDATE", "REVIEW") and not state.last_validation_passed:
        problems.append("the latest validation did not pass")
    if (source, to) == ("VALIDATE", "IMPLEMENT") and reason == "validation_failed":
        if state.last_validation_passed:
            problems.append("validation passed; refusing the failure return")
        if state.validate_failures < 1 or state.validate_failures >= state.max_validate_attempts:
            problems.append("failure return is outside the attempt window")
    if (source, to) == ("VALIDATE", "FAILED") and state.validate_failures < state.max_validate_attempts:
        problems.append("attempts are not exhausted")
    if (source, to) == ("REVIEW", "DELIVERY"):
        if state.reviewer_id is None or state.developer_id is None:
            problems.append("reviewer and developer must both be set")
        elif state.reviewer_id.casefold() == state.developer_id.casefold():
            problems.append("reviewer and developer are the same actor")
        if not (engine.run_dir / "review.json").is_file():
            problems.append("review.json is missing")
    if (source, to) == ("DELIVERY", "MEMORY") and not state.delivery_ready:
        problems.append("delivery.md has not been composed")
    if (source, to) == ("MEMORY", "DONE") and reason == "memory_recorded":
        if not engine._config().memory.enabled:
            problems.append("memory is disabled")
        config = engine._config()
        if config.workflow.memory_write_command:
            if state.memory_remote_status != "confirmed":
                problems.append("remote memory is not confirmed")
            if not state.memory_ack_page:
                problems.append("memory page path is missing after sync")
        elif not state.memory_ack_page:
            problems.append("memory page has not been acked")
    if (source, to) == ("MEMORY", "DONE") and reason == "memory_skipped":
        if engine._config().memory.enabled:
            problems.append("memory is enabled")
        if not state.memory_skipped_reason:
            problems.append("memory skip reason is missing")
    return problems


def park_run(
    engine: Engine,
    to: str | None,
    reason: str,
    role: str,
    actor_id: str,
    action: str,
) -> None:
    state = engine.ensure()
    state.resume_status = state.status
    state.pending_to = to
    state.pending_reason = reason
    state.pending_role = role
    state.pending_actor = actor_id
    state.pending_action = action
    state.status = "WAITING_APPROVAL"
    state.updated_at = utc_now()
    engine._save()
    engine._event("waiting_approval", action=action, dest=to, actor_id=actor_id)


def apply_transition(
    engine: Engine,
    to: str,
    role: str,
    actor_id: str,
    reason: str,
    internal: bool,
) -> None:
    state = engine.ensure()
    source = state.status
    edge = (source, to)
    if edge not in EDGES or reason not in EDGES[edge]:
        raise InvalidTransition(f"{source} -> {to} ({reason}) is not defined")
    if edge in INTERNAL_ONLY and not internal:
        raise InvalidTransition(f"{source} -> {to} is gated by an engine operation")
    if role not in EDGE_ROLES[edge]:
        raise PolicyError(f"role {role} cannot take {source} -> {to}")
    problems = check_preconditions(engine, source, to, reason)
    if problems:
        raise PreconditionError(problems)
    if not internal and source == "INTAKE" and to == "RESEARCH" and state.risk == "HIGH":
        if "start_high_risk" not in state.approvals:
            park_run(engine, to, reason, role, actor_id, "start_high_risk")
            return
    if to == "IMPLEMENT":
        engine._prepare_branch()
    if to in {"IMPLEMENT", "PLAN"} and reason in RESET_REASONS:
        state.last_validation_passed = False
        state.implementation_ready = False
    state.status = to
    state.updated_at = utc_now()
    if to == "MEMORY":
        engine._write_memory_payload()
    engine._save()
    engine._event("transition", source=source, dest=to, reason=reason, role=role, actor_id=actor_id)
