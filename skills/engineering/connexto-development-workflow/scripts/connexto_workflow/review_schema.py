"""Shared review finding schema for developer and judge payloads."""

from __future__ import annotations

from dataclasses import dataclass

from connexto_workflow.errors import PreconditionError

_SEVERITIES = frozenset({"critical", "blocking", "important", "minor"})
_RETURN_TARGETS = frozenset({"IMPLEMENT", "PLAN"})


@dataclass(frozen=True)
class Finding:
    severity: str
    file: str
    location: str
    rationale: str
    return_to: str


def parse_review(payload: dict[str, object]) -> tuple[str, list[Finding]]:
    summary = payload.get("summary")
    raw_findings = payload.get("findings")
    if not isinstance(summary, str) or not summary.strip():
        raise PreconditionError(["review summary is empty"])
    if not isinstance(raw_findings, list):
        raise PreconditionError(["review findings must be a list"])
    findings: list[Finding] = []
    for item in raw_findings:
        if not isinstance(item, dict):
            raise PreconditionError(["each finding must be an object"])
        severity = item.get("severity")
        file_name = item.get("file")
        location = item.get("location")
        rationale = item.get("rationale")
        return_to = item.get("return_to", "IMPLEMENT")
        if severity not in _SEVERITIES:
            raise PreconditionError([f"invalid severity: {severity}"])
        if not isinstance(file_name, str) or not file_name.strip():
            raise PreconditionError(["finding file is empty"])
        if not isinstance(location, str) or not location.strip():
            raise PreconditionError(["finding location is empty"])
        if not isinstance(rationale, str) or not rationale.strip():
            raise PreconditionError(["finding rationale is empty"])
        if return_to not in _RETURN_TARGETS:
            raise PreconditionError([f"invalid return_to: {return_to}"])
        findings.append(
            Finding(
                severity=str(severity),
                file=file_name.strip(),
                location=location.strip(),
                rationale=rationale.strip(),
                return_to=str(return_to),
            )
        )
    return summary.strip(), findings
