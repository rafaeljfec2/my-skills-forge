"""Delivery state machine. Chat history is not the source of recovery."""

from __future__ import annotations

import json
from pathlib import Path

from connexto_workflow.config import CONFIG_FILENAME, ProjectConfig, load_config
from connexto_workflow.developer_flow import DeveloperFlowMixin
from connexto_workflow.engine_support import (
    ACTOR_ID,
    ROLES,
    Brief,
    effective_risk,
    require_demand_id,
    require_demand_type,
    require_text,
    utc_now,
)
from connexto_workflow.errors import ConfigError, PolicyError, WorkflowError
from connexto_workflow.git_ops import GitOpsMixin
from connexto_workflow.memory_flow import MemoryFlowMixin
from connexto_workflow.model import next_step_for
from connexto_workflow.operator_flow import OperatorFlowMixin
from connexto_workflow.redact import redact
from connexto_workflow.render import render_brief
from connexto_workflow.review_flow import ReviewFlowMixin
from connexto_workflow.state import RunState, atomic_write, load_state
from connexto_workflow.transition_ops import apply_transition

__all__ = ["Brief", "Engine"]


class Engine(
    GitOpsMixin,
    DeveloperFlowMixin,
    ReviewFlowMixin,
    MemoryFlowMixin,
    OperatorFlowMixin,
):
    """One demand directory under `<repo>/.connexto/runs/<id>`."""

    def __init__(self, repo: Path, demand_id: str) -> None:
        self.repo = repo.resolve()
        self.demand_id = demand_id
        self.run_dir = self.repo / ".connexto" / "runs" / demand_id
        self.state: RunState | None = None
        self.config: ProjectConfig | None = None

    def init_run(self, brief: Brief, config_path: Path | None = None) -> RunState:
        demand_type = require_demand_type(brief.demand_type)
        demand_id = require_demand_id(brief.demand_id, demand_type)
        if demand_id != self.demand_id:
            raise ConfigError("brief demand_id does not match the engine demand id")
        if self.run_dir.exists():
            raise WorkflowError(f"run already exists: {self.run_dir}")
        require_text(brief.problem, "problem")
        require_text(brief.desired_outcome, "desired_outcome")
        require_text(brief.scope, "scope")
        require_text(brief.target_project, "target_project")
        if not brief.success_criteria or any(not item.strip() for item in brief.success_criteria):
            raise ConfigError("success_criteria must contain at least one non-empty item")
        path = config_path or (self.repo / CONFIG_FILENAME)
        config = load_config(path)
        if brief.target_project != config.project.name:
            raise ConfigError("brief target_project does not match project.name")
        risk = effective_risk(demand_type, brief.risk)
        self.config = config
        now = utc_now()
        self.state = RunState(
            demand_id=demand_id,
            demand_type=demand_type,
            status="PENDING",
            risk=risk,
            target_project=brief.target_project,
            objective=brief.desired_outcome.strip(),
            max_validate_attempts=config.quality.max_validate_attempts,
            max_review_rounds=config.workflow.max_review_rounds,
            updated_at=now,
        )
        self.run_dir.mkdir(parents=True)
        (self.run_dir / "evidence").mkdir()
        (self.run_dir / "memory").mkdir()
        snapshot = json.dumps(json.loads(path.read_text(encoding="utf-8")), indent=2) + "\n"
        atomic_write(self.run_dir / "project.snapshot.json", snapshot)
        atomic_write(self.run_dir / "brief.md", render_brief(brief, risk, now))
        self._save()
        self._event("init", risk=risk, project=config.project.name)
        return self.state

    def load(self) -> RunState:
        state_path = self.run_dir / "state.json"
        if not state_path.is_file():
            raise WorkflowError(f"no run state at {state_path}")
        require_demand_id(self.demand_id, None)
        self.state = load_state(state_path)
        if self.state.demand_id != self.demand_id:
            raise WorkflowError("state demand_id does not match this engine")
        self.config = load_config(self.run_dir / "project.snapshot.json")
        return self.state

    def ensure(self) -> RunState:
        if self.state is None or self.config is None:
            return self.load()
        return self.state

    def status_view(self) -> dict[str, object]:
        state = self.ensure()
        return {
            "demand_id": state.demand_id,
            "status": state.status,
            "risk": state.risk,
            "next_step": next_step_for(state.status, state.pending_action),
            "validate_failures": state.validate_failures,
            "max_validate_attempts": state.max_validate_attempts,
            "developer_id": state.developer_id,
            "reviewer_id": state.reviewer_id,
            "git_branch": state.git_branch,
            "git_commit": state.git_commit,
            "pending_action": state.pending_action,
            "pending_to": state.pending_to,
            "blocked_dependency": state.blocked_dependency,
            "memory_ack_page": state.memory_ack_page,
            "run_dir": str(self.run_dir),
        }

    def request_transition(self, to: str, role: str, actor_id: str, reason: str) -> RunState:
        self._check_actor(role, actor_id)
        apply_transition(self, to, role, actor_id, reason, internal=False)
        return self.ensure()

    def _apply(self, to: str, role: str, actor_id: str, reason: str, internal: bool) -> None:
        apply_transition(self, to, role, actor_id, reason, internal)

    def _bind_developer(self, actor_id: str) -> None:
        state = self.ensure()
        if state.developer_id is None:
            state.developer_id = actor_id
            return
        if state.developer_id != actor_id:
            raise PolicyError("a different developer already owns this run")

    def command_records(self) -> list[dict[str, object]]:
        self.ensure()
        return self._command_records()

    def _command_records(self) -> list[dict[str, object]]:
        path = self._commands_log()
        if not path.is_file():
            return []
        records: list[dict[str, object]] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            item = json.loads(line)
            if isinstance(item, dict):
                records.append(item)
        return records

    def _review_summary(self) -> str:
        path = self.run_dir / "review.json"
        if not path.is_file():
            return "review file missing"
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return "review file invalid"
        summary = data.get("summary", "")
        findings = data.get("findings", [])
        count = len(findings) if isinstance(findings, list) else 0
        return f"{summary} Findings: {count}."

    def _read_optional(self, name: str) -> str:
        path = self.run_dir / name
        if not path.is_file():
            return ""
        return path.read_text(encoding="utf-8")

    def _commands_log(self) -> Path:
        return self.run_dir / "evidence" / "commands.jsonl"

    def _config(self) -> ProjectConfig:
        self.ensure()
        if self.config is None:
            raise WorkflowError("config is not loaded")
        return self.config

    def _save(self) -> None:
        if self.state is None:
            raise WorkflowError("state is not loaded")
        self.state.updated_at = utc_now()
        atomic_write(self.run_dir / "state.json", self.state.to_json())

    def _event(self, kind: str, **fields: object) -> None:
        state = self.ensure()
        payload: dict[str, object] = {
            "at": utc_now(),
            "kind": kind,
            "demand_id": state.demand_id,
            "status": state.status,
        }
        for key, value in fields.items():
            payload[key] = redact(value) if isinstance(value, str) else value
        path = self.run_dir / "evidence" / "execution.jsonl"
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")

    def _check_actor(self, role: str, actor_id: str) -> None:
        if role not in ROLES:
            raise PolicyError(f"unknown role: {role}")
        if not ACTOR_ID.match(actor_id):
            raise PolicyError("actor id is invalid")
