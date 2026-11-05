"""Persisted run checkpoint. Recovery reads this file, not the chat transcript."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass
class RunState:
    schema_version: int = 2
    demand_id: str = ""
    demand_type: str = ""
    status: str = "PENDING"
    risk: str = ""
    target_project: str = ""
    objective: str = ""
    developer_id: str | None = None
    reviewer_id: str | None = None
    developer_session_id: str | None = None
    reviewer_session_id: str | None = None
    review_round: int = 0
    max_review_rounds: int = 3
    validate_failures: int = 0
    max_validate_attempts: int = 3
    last_validation_passed: bool = False
    implementation_ready: bool = False
    implement_hook_succeeded: bool = False
    delivery_ready: bool = False
    pending_to: str | None = None
    pending_reason: str | None = None
    pending_action: str | None = None
    pending_actor: str | None = None
    pending_role: str | None = None
    resume_status: str | None = None
    approvals: list[str] = field(default_factory=list)
    failures: list[dict[str, str]] = field(default_factory=list)
    decisions: list[str] = field(default_factory=list)
    git_branch: str | None = None
    git_commit: str | None = None
    memory_ack_page: str | None = None
    memory_skipped_reason: str | None = None
    memory_remote_status: str = "none"
    memory_page_id: str | None = None
    memory_body_sha256: str | None = None
    memory_sync_attempts: int = 0
    blocked_dependency: str | None = None
    updated_at: str = ""

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2, ensure_ascii=False) + "\n"


def load_state(path: Path) -> RunState:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"state file is not an object: {path}")
    version = data.get("schema_version", 1)
    if version not in (1, 2):
        raise ValueError(f"unsupported state schema in {path}")
    known = set(RunState.__dataclass_fields__)
    filtered = {key: value for key, value in data.items() if key in known}
    defaults = RunState()
    for key in known:
        filtered.setdefault(key, getattr(defaults, key))
    filtered["schema_version"] = 2
    return RunState(**filtered)


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)
