"""Remote AI Memory sync with explicit lifecycle states."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from connexto_workflow.backends import BackendResult, parse_json_stdout, run_backend
from connexto_workflow.errors import PreconditionError, WorkflowError

MEMORY_STATUSES = frozenset({"none", "prepared", "sent", "confirmed", "pending_sync", "local_ack"})


@dataclass(frozen=True)
class MemoryWriteResult:
    page_path: str
    page_id: str | None
    body_sha256: str


def memory_dir(run_dir: Path) -> Path:
    return run_dir / "memory"


def prepare_body(run_dir: Path, payload: dict[str, object]) -> tuple[Path, str]:
    directory = memory_dir(run_dir)
    directory.mkdir(parents=True, exist_ok=True)
    body_path = directory / "body.md"
    text = _render_body(payload)
    body_path.write_text(text, encoding="utf-8")
    digest = _sha256(text)
    sync_request = {
        "status": "prepared",
        "body_sha256": digest,
        "page_path": payload.get("page_path"),
        "idempotency_key": payload.get("demand_id"),
    }
    (directory / "sync-request.json").write_text(
        json.dumps(sync_request, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return body_path, digest


def execute_write(
    command: str,
    repo: Path,
    timeout: int,
    env: dict[str, str],
) -> MemoryWriteResult:
    result = run_backend(command, env, repo, timeout)
    data = parse_json_stdout(result, "memory write backend")
    page_path = data.get("page_path")
    if not isinstance(page_path, str) or not page_path.strip():
        raise WorkflowError("memory write backend must return page_path")
    page_id = data.get("page_id")
    if page_id is not None and (not isinstance(page_id, str) or not page_id.strip()):
        raise WorkflowError("memory page_id must be a string when present")
    body_sha256 = data.get("body_sha256")
    if not isinstance(body_sha256, str) or len(body_sha256) != 64:
        raise WorkflowError("memory write backend must return body_sha256 (sha256 hex)")
    return MemoryWriteResult(
        page_path=page_path.strip(),
        page_id=page_id.strip() if isinstance(page_id, str) else None,
        body_sha256=body_sha256.strip(),
    )


def execute_read(command: str, repo: Path, timeout: int, env: dict[str, str]) -> str:
    result = run_backend(command, env, repo, timeout)
    if not result.passed:
        detail = result.stderr.strip() or result.stdout.strip() or "memory read backend failed"
        raise WorkflowError(detail)
    return result.stdout


def verify_read_body(body: str, demand_id: str, expected_sha256: str) -> None:
    if demand_id not in body:
        raise PreconditionError(["read body does not contain demand id"])
    actual = _sha256(body)
    if actual != expected_sha256:
        raise PreconditionError(["read body sha256 does not match prepared payload"])


def record_sync_attempt(run_dir: Path, attempt: int, status: str, detail: str) -> None:
    directory = memory_dir(run_dir)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "sync-log.jsonl"
    payload = {"attempt": attempt, "status": status, "detail": detail}
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def _render_body(payload: dict[str, object]) -> str:
    demand_id = payload.get("demand_id", "")
    return (
        f"# Run {demand_id}\n\n"
        f"```json\n{json.dumps(payload, indent=2, ensure_ascii=False)}\n```\n"
    )


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
