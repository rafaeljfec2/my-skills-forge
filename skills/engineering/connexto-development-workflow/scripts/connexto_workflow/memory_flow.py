"""Memory payload, ack, sync, and skip."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from connexto_workflow.engine_support import PAGE, require_text
from connexto_workflow.errors import InvalidTransition, PolicyError, PreconditionError, WorkflowError
from connexto_workflow.memory_sync import (
    execute_read,
    execute_write,
    prepare_body,
    record_sync_attempt,
    verify_read_body,
)
from connexto_workflow.redact import contains_secret
from connexto_workflow.state import RunState, atomic_write

if TYPE_CHECKING:
    from connexto_workflow.engine import Engine


class MemoryFlowMixin:
    def _write_memory_payload(self: Engine) -> None:
        state = self.ensure()
        config = self._config()
        review_path = self.run_dir / "review.json"
        review: object = None
        if review_path.is_file():
            review = json.loads(review_path.read_text(encoding="utf-8"))
        payload: dict[str, object] = {
            "demand_id": state.demand_id,
            "demand_type": state.demand_type,
            "project": state.target_project,
            "workspace": config.memory.workspace,
            "memory_project": config.memory.project,
            "objective": state.objective,
            "risk": state.risk,
            "status": state.status,
            "decisions": list(state.decisions),
            "failures": list(state.failures),
            "commands": self._command_records(),
            "review": review,
            "git_branch": state.git_branch,
            "git_commit": state.git_commit,
            "artifacts": sorted(path.name for path in self.run_dir.iterdir() if path.is_file()),
            "run_dir": str(self.run_dir),
        }
        atomic_write(
            self.run_dir / "memory" / "payload.json",
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        )

    def memory_payload(self: Engine) -> dict[str, object]:
        self.ensure()
        path = self.run_dir / "memory" / "payload.json"
        if not path.is_file():
            self._write_memory_payload()
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise WorkflowError("memory payload is not an object")
        return data

    def ack_memory(self: Engine, role: str, actor_id: str, page: str) -> RunState:
        self._check_actor(role, actor_id)
        state = self.ensure()
        config = self._config()
        if config.workflow.memory_write_command:
            raise PolicyError("remote memory is configured; use memory-sync instead of memory-ack")
        if not config.memory.enabled:
            raise PolicyError("memory is disabled; call skip_memory")
        if state.status != "MEMORY":
            raise InvalidTransition("memory ack is accepted only in MEMORY")
        if role != "orchestrator":
            raise PolicyError("only the orchestrator can ack memory")
        if not PAGE.match(page) or ".." in page.split("/"):
            raise PolicyError("memory page path is invalid")
        if contains_secret(page):
            raise PolicyError("memory page path contains credential-shaped text")
        if not (self.run_dir / "memory" / "payload.json").is_file():
            raise PreconditionError(["memory payload is missing"])
        state.memory_ack_page = page
        state.memory_remote_status = "local_ack"
        self._save()
        self._apply("DONE", role, actor_id, "memory_recorded", internal=True)
        return self.ensure()

    def sync_memory(self: Engine, role: str, actor_id: str) -> RunState:
        self._check_actor(role, actor_id)
        state = self.ensure()
        config = self._config()
        if not config.memory.enabled:
            raise PolicyError("memory is disabled; call skip_memory")
        if state.status != "MEMORY":
            raise InvalidTransition("memory sync runs only in MEMORY")
        if role != "orchestrator":
            raise PolicyError("only the orchestrator can sync memory")
        write_command = config.workflow.memory_write_command
        read_command = config.workflow.memory_read_command
        if not write_command or not read_command:
            raise PolicyError("memory sync requires workflow.memory_write_command and memory_read_command")
        payload = self.memory_payload()
        payload["page_path"] = f"runs/{state.demand_id}.md"
        body_path, digest = prepare_body(self.run_dir, payload)
        state.memory_remote_status = "prepared"
        state.memory_body_sha256 = digest
        state.memory_sync_attempts += 1
        self._save()
        attempt = state.memory_sync_attempts
        env = {
            "CDW_MEMORY_WORKSPACE": config.memory.workspace or "",
            "CDW_MEMORY_PROJECT": config.memory.project or "",
            "CDW_MEMORY_PATH": payload["page_path"],
            "CDW_MEMORY_BODY_FILE": str(body_path),
            "CDW_MEMORY_IDEMPOTENCY_KEY": state.demand_id,
            "CDW_MEMORY_ATTEMPT": str(attempt),
        }
        try:
            write_result = execute_write(
                write_command,
                self.repo,
                config.quality.command_timeout_seconds,
                env,
            )
        except WorkflowError as exc:
            state.memory_remote_status = "pending_sync"
            record_sync_attempt(self.run_dir, attempt, "pending_sync", str(exc))
            self._save()
            raise
        if write_result.body_sha256 != digest:
            state.memory_remote_status = "pending_sync"
            record_sync_attempt(self.run_dir, attempt, "hash_mismatch", "write backend hash mismatch")
            self._save()
            raise PolicyError("memory write backend returned a mismatched body hash")
        state.memory_remote_status = "sent"
        state.memory_ack_page = write_result.page_path
        state.memory_page_id = write_result.page_id
        self._save()
        read_env = dict(env)
        read_env["CDW_MEMORY_PAGE_PATH"] = write_result.page_path
        if write_result.page_id:
            read_env["CDW_MEMORY_PAGE_ID"] = write_result.page_id
        try:
            body = execute_read(read_command, self.repo, config.quality.command_timeout_seconds, read_env)
        except WorkflowError as exc:
            state.memory_remote_status = "pending_sync"
            record_sync_attempt(self.run_dir, attempt, "read_failed", str(exc))
            self._save()
            raise
        verify_read_body(body, state.demand_id, digest)
        state.memory_remote_status = "confirmed"
        record_sync_attempt(self.run_dir, attempt, "confirmed", write_result.page_path)
        self._save()
        self._apply("DONE", role, actor_id, "memory_recorded", internal=True)
        return self.ensure()

    def skip_memory(self: Engine, role: str, actor_id: str, reason: str) -> RunState:
        self._check_actor(role, actor_id)
        state = self.ensure()
        if self._config().memory.enabled:
            raise PolicyError("memory is enabled; ack a page instead of skipping")
        if state.status != "MEMORY":
            raise InvalidTransition("memory skip is accepted only in MEMORY")
        if role != "orchestrator":
            raise PolicyError("only the orchestrator can skip memory")
        require_text(reason, "reason")
        state.memory_skipped_reason = reason.strip()
        self._save()
        self._apply("DONE", role, actor_id, "memory_skipped", internal=True)
        return self.ensure()
