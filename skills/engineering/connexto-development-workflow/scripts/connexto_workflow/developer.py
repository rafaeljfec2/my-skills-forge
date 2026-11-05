"""Developer task bundle and implementation report contract."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from connexto_workflow.errors import PreconditionError, WorkflowError
from connexto_workflow.redact import contains_secret

if TYPE_CHECKING:
    from connexto_workflow.engine import Engine

REPORT_VERSION = 1
REQUIRED_REPORT_KEYS = (
    "summary",
    "files_changed",
    "tests_touched",
    "commands_run",
    "results",
    "issues",
    "pending",
    "evidence_refs",
)


@dataclass(frozen=True)
class DeveloperReport:
    summary: str
    files_changed: list[str]
    tests_touched: list[str]
    commands_run: list[dict[str, object]]
    results: list[str]
    issues: list[str]
    pending: list[str]
    evidence_refs: list[str]
    developer_session_id: str | None = None


def developer_dir(run_dir: Path) -> Path:
    return run_dir / "developer"


def build_task_package(engine: Engine) -> dict[str, object]:
    """Structured inputs for the Developer. No implementation conclusions."""
    state = engine.ensure()
    config = engine._config()
    package: dict[str, object] = {
        "demand_id": state.demand_id,
        "demand_type": state.demand_type,
        "risk": state.risk,
        "objective": state.objective,
        "target_project": state.target_project,
        "repo": str(engine.repo),
        "artifacts": {
            name: _read_if_exists(engine.run_dir / name)
            for name in ("brief.md", "research.md", "spec.md", "plan.md", "tasks.md")
        },
        "project": {
            "name": config.project.name,
            "language": config.project.language,
            "framework": config.project.framework,
        },
        "commands": config.commands.as_dict(),
        "quality": {
            "require_tests": config.quality.require_tests,
            "require_lint": config.quality.require_lint,
            "require_typecheck": config.quality.require_typecheck,
            "require_build": config.quality.require_build,
        },
        "constraints": {
            "implement_command_optional": config.commands.implement is None,
            "developer_must_edit_repo_when_implement_null": config.commands.implement is None,
        },
    }
    findings = engine.run_dir / "review" / "findings-for-developer.json"
    if findings.is_file():
        package["review_findings"] = json.loads(findings.read_text(encoding="utf-8"))
    return package


def write_task_files(engine: Engine) -> Path:
    directory = developer_dir(engine.run_dir)
    directory.mkdir(parents=True, exist_ok=True)
    package = build_task_package(engine)
    task_json = directory / "task.json"
    task_json.write_text(json.dumps(package, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    task_md = directory / "task.md"
    task_md.write_text(_render_task_md(package), encoding="utf-8")
    return task_json


def parse_report(payload: dict[str, object]) -> DeveloperReport:
    version = payload.get("report_version", 1)
    if version != REPORT_VERSION:
        raise PreconditionError([f"unsupported report_version: {version}"])
    missing = [key for key in REQUIRED_REPORT_KEYS if key not in payload]
    if missing:
        raise PreconditionError([f"developer report missing keys: {', '.join(missing)}"])
    summary = payload.get("summary")
    if not isinstance(summary, str) or not summary.strip():
        raise PreconditionError(["developer report summary is empty"])
    files_changed = _string_list(payload.get("files_changed"), "files_changed")
    tests_touched = _string_list(payload.get("tests_touched"), "tests_touched")
    results = _string_list(payload.get("results"), "results")
    issues = _string_list(payload.get("issues"), "issues")
    pending = _string_list(payload.get("pending"), "pending")
    evidence_refs = _string_list(payload.get("evidence_refs"), "evidence_refs")
    commands_run = payload.get("commands_run")
    if not isinstance(commands_run, list):
        raise PreconditionError(["commands_run must be a list"])
    normalized_commands: list[dict[str, object]] = []
    for item in commands_run:
        if not isinstance(item, dict):
            raise PreconditionError(["each commands_run entry must be an object"])
        normalized_commands.append(item)
    session = payload.get("developer_session_id")
    if session is not None and (not isinstance(session, str) or not session.strip()):
        raise PreconditionError(["developer_session_id must be a string when present"])
    if contains_secret(summary):
        raise PreconditionError(["developer report summary contains credential-shaped text"])
    return DeveloperReport(
        summary=summary.strip(),
        files_changed=files_changed,
        tests_touched=tests_touched,
        commands_run=normalized_commands,
        results=results,
        issues=issues,
        pending=pending,
        evidence_refs=evidence_refs,
        developer_session_id=session.strip() if isinstance(session, str) else None,
    )


def validate_report_against_repo(report: DeveloperReport, repo: Path) -> list[str]:
    problems: list[str] = []
    if not report.files_changed and not report.tests_touched:
        problems.append("developer report must list at least one changed file or test")
    if not report.results:
        problems.append("developer report must include at least one result line")
    if not report.evidence_refs:
        problems.append("developer report must reference evidence paths")
    for rel in report.files_changed + report.tests_touched:
        if rel.startswith("/") or ".." in Path(rel).parts:
            problems.append(f"refusing path in report: {rel}")
            continue
        path = repo / rel
        if not path.is_file():
            problems.append(f"report references missing file: {rel}")
    for ref in report.evidence_refs:
        if ".." in ref or ref.startswith("/"):
            problems.append(f"invalid evidence ref: {ref}")
    for item in report.commands_run:
        exit_code = item.get("exit_code")
        if exit_code is None:
            problems.append("each commands_run entry must include exit_code")
    return problems


def _string_list(value: object, label: str) -> list[str]:
    if not isinstance(value, list):
        raise PreconditionError([f"{label} must be a list"])
    items: list[str] = []
    for entry in value:
        if not isinstance(entry, str) or not entry.strip():
            raise PreconditionError([f"{label} entries must be non-empty strings"])
        items.append(entry.strip())
    return items


def _read_if_exists(path: Path) -> str | None:
    if not path.is_file():
        return None
    return path.read_text(encoding="utf-8")


def _render_task_md(package: dict[str, object]) -> str:
    demand_id = package.get("demand_id", "")
    objective = package.get("objective", "")
    return (
        f"# Developer task\n\n"
        f"- Demand: {demand_id}\n\n"
        f"## Objective\n{objective}\n\n"
        f"Read `developer/task.json` for the full structured bundle. "
        f"Do not treat researcher or planner text as implementation evidence.\n"
    )
