"""Markdown render helpers for run artifacts."""

from __future__ import annotations

from connexto_workflow.commands import CommandRecord
from connexto_workflow.engine_support import RELEASE_KEYS, Brief
from connexto_workflow.review_schema import Finding
from connexto_workflow.state import RunState


def shlex_join(argv: object) -> str:
    if not isinstance(argv, list):
        return ""
    return " ".join(str(part) for part in argv)


def render_brief(brief: Brief, risk: str, now: str) -> str:
    criteria = "\n".join(f"- {item.strip()}" for item in brief.success_criteria)
    constraints = "\n".join(f"- {item.strip()}" for item in brief.constraints) or "- none"
    return (
        f"# Brief\n\n"
        f"- Demand: {brief.demand_id}\n"
        f"- State: PENDING\n"
        f"- Date: {now}\n"
        f"- Owner: orchestrator\n"
        f"- Type: {brief.demand_type}\n"
        f"- Risk: {risk}\n"
        f"- Target project: {brief.target_project}\n\n"
        f"## Problem\n{brief.problem.strip()}\n\n"
        f"## Desired outcome\n{brief.desired_outcome.strip()}\n\n"
        f"## Scope\n{brief.scope.strip()}\n\n"
        f"## Success criteria\n{criteria}\n\n"
        f"## Constraints\n{constraints}\n"
    )


def render_validation(demand_id: str, results: list[CommandRecord]) -> str:
    lines = [f"# Validation\n", f"- Demand: {demand_id}\n", "\n## Commands\n"]
    for result in results:
        rendered = "timeout" if result.timed_out else str(result.exit_code)
        lines.append(f"- {result.name}: exit {rendered} argv `{shlex_join(result.argv)}`\n")
    return "".join(lines)


def render_review(demand_id: str, reviewer: str, summary: str, findings: list[Finding]) -> str:
    rows = [
        "# Review\n",
        f"- Demand: {demand_id}\n",
        f"- Reviewer: {reviewer}\n",
        "\n## Summary\n",
        summary,
        "\n\n## Findings\n",
    ]
    if not findings:
        rows.append("- none\n")
    for item in findings:
        rows.append(
            f"- {item.severity} `{item.file}` ({item.location}): {item.rationale} → {item.return_to}\n"
        )
    return "".join(rows)


def render_delivery(
    demand_id: str,
    state: RunState,
    sections: dict[str, str],
    commands: list[dict[str, object]],
    review_summary: str,
) -> str:
    command_lines = ["- none recorded"]
    if commands:
        command_lines = []
        for record in commands:
            exit_code = record.get("exit_code")
            rendered = "timeout" if record.get("timed_out") else str(exit_code)
            command_lines.append(f"- {record.get('name')}: exit {rendered}")
    release = [f"- {key}: not performed" for key in RELEASE_KEYS]
    branch = state.git_branch or "not created"
    commit = state.git_commit or "not created"
    return (
        f"# Delivery\n\n"
        f"- Demand: {demand_id}\n"
        f"- State: DELIVERY\n"
        f"- Owner: orchestrator\n\n"
        f"## Problem solved\n{sections['problem_solved'].strip()}\n\n"
        f"## Solution\n{sections['solution'].strip()}\n\n"
        f"## Files changed\n{sections['files_changed'].strip()}\n\n"
        f"## Validation\n" + "\n".join(command_lines) + "\n\n"
        f"## Review\n{review_summary}\n\n"
        f"## Git\n- branch: {branch}\n- commit: {commit}\n\n"
        f"## Limitations\n{sections['limitations'].strip()}\n\n"
        f"## Follow-ups\n{sections['follow_ups'].strip()}\n\n"
        f"## Release actions\n" + "\n".join(release) + "\n"
    )
