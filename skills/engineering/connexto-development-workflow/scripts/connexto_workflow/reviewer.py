"""Independent reviewer bundle for senior-code-review-judge."""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from connexto_workflow.errors import PreconditionError, WorkflowError
from connexto_workflow.redact import contains_secret
from connexto_workflow.review_schema import Finding, parse_review
from connexto_workflow.state import RunState

if TYPE_CHECKING:
    pass

JUDGE_SKILL = "senior-code-review-judge"
APPROVED_VERDICTS = frozenset({"APPROVED"})
NOTES_VERDICTS = frozenset({"APPROVED_WITH_NOTES"})


@dataclass(frozen=True)
class JudgeVerdict:
    verdict: str
    summary: str
    findings: list[Finding]
    reviewer_session_id: str
    round_number: int
    skill: str


def review_dir(run_dir: Path) -> Path:
    return run_dir / "review"


def write_findings_for_developer(run_dir: Path, findings: list[Finding]) -> None:
    directory = review_dir(run_dir)
    directory.mkdir(parents=True, exist_ok=True)
    payload = {
        "findings": [item.__dict__ for item in findings],
    }
    (directory / "findings-for-developer.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def build_judge_bundle(
    run_dir: Path,
    repo: Path,
    state: RunState,
    command_records: list[dict[str, object]],
    reviewer_session_id: str,
    round_number: int,
) -> Path:
    """Inputs visible to the judge. Excludes developer private reasoning."""
    directory = review_dir(run_dir) / "judge-input"
    directory.mkdir(parents=True, exist_ok=True)
    diff = _git_diff(repo)
    bundle: dict[str, object] = {
        "skill": JUDGE_SKILL,
        "demand_id": state.demand_id,
        "reviewer_session_id": reviewer_session_id,
        "developer_session_id": state.developer_session_id,
        "developer_actor_id": state.developer_id,
        "round": round_number,
        "risk": state.risk,
        "acceptance": {
            "brief": _read(run_dir / "brief.md"),
            "spec": _read(run_dir / "spec.md"),
            "plan": _read(run_dir / "plan.md"),
            "tasks": _read(run_dir / "tasks.md"),
        },
        "validation": _read(run_dir / "validation.md"),
        "command_records": command_records,
        "diff": diff,
        "forbidden_inputs": [
            "developer/report.json summary alone",
            "developer private chain-of-thought",
        ],
    }
    out = directory / "bundle.json"
    out.write_text(json.dumps(bundle, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return out


def parse_judge_output(payload: dict[str, object]) -> JudgeVerdict:
    skill = payload.get("skill", JUDGE_SKILL)
    if skill != JUDGE_SKILL:
        raise PreconditionError([f"judge skill must be {JUDGE_SKILL}"])
    verdict = payload.get("verdict")
    if not isinstance(verdict, str) or not verdict.strip():
        raise PreconditionError(["judge verdict is missing"])
    session = payload.get("reviewer_session_id")
    if not isinstance(session, str) or not session.strip():
        raise PreconditionError(["reviewer_session_id is required"])
    round_number = payload.get("round")
    if isinstance(round_number, bool) or not isinstance(round_number, int) or round_number < 1:
        raise PreconditionError(["round must be a positive integer"])
    summary, findings = parse_review(
        {
            "summary": payload.get("summary", ""),
            "findings": payload.get("findings", []),
        }
    )
    if contains_secret(summary):
        raise PreconditionError(["judge summary contains credential-shaped text"])
    return JudgeVerdict(
        verdict=verdict.strip().upper(),
        summary=summary,
        findings=findings,
        reviewer_session_id=session.strip(),
        round_number=round_number,
        skill=str(skill),
    )


def verdict_blocks_delivery(verdict: JudgeVerdict, risk: str) -> bool:
    from connexto_workflow.model import BLOCKING_SEVERITIES

    if verdict.verdict in APPROVED_VERDICTS and not verdict.findings:
        return False
    if verdict.verdict in NOTES_VERDICTS:
        blocking = [item for item in verdict.findings if item.severity in BLOCKING_SEVERITIES[risk]]
        return bool(blocking)
    if verdict.verdict in {"REJECTED", "INCOMPLETE"}:
        return True
    blocking = [item for item in verdict.findings if item.severity in BLOCKING_SEVERITIES[risk]]
    return bool(blocking)


def _git_diff(repo: Path) -> str:
    if not (repo / ".git").exists():
        return ""
    completed = subprocess.run(
        ["git", "diff", "HEAD"],
        cwd=str(repo),
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        return completed.stderr or ""
    return completed.stdout


def _read(path: Path) -> str:
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8")
