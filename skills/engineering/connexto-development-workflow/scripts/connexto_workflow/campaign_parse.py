"""Sprint queue parser. Each sprint is exactly four tasks."""

from __future__ import annotations

import re
from dataclasses import dataclass

from connexto_workflow.engine_support import work_branch_error
from connexto_workflow.errors import ConfigError

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
        branch_error = work_branch_error(feature.group(2))
        if branch_error is not None:
            raise ConfigError(f"sprint {match.group(1)}: {branch_error}")
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
