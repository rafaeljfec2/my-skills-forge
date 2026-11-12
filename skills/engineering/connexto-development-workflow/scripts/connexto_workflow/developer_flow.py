"""Developer task, backend, report, and implement hook."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from connexto_workflow.backends import run_backend
from connexto_workflow.commands import run_command
from connexto_workflow.developer import (
    developer_dir,
    parse_report,
    validate_report_against_repo,
    write_task_files,
)
from connexto_workflow.engine_support import command_detail, require_text, utc_now
from connexto_workflow.errors import InvalidTransition, PolicyError, PreconditionError, WorkflowError
from connexto_workflow.redact import contains_secret
from connexto_workflow.state import RunState, atomic_write

if TYPE_CHECKING:
    from connexto_workflow.engine import Engine


class DeveloperFlowMixin:
    def materialize_developer_task(
        self: Engine,
        role: str,
        actor_id: str,
        developer_session_id: str,
    ) -> RunState:
        self._check_actor(role, actor_id)
        state = self.ensure()
        if state.status != "IMPLEMENT":
            raise InvalidTransition("developer task materialization runs only in IMPLEMENT")
        if role != "developer":
            raise PolicyError("only the developer role can receive the task bundle")
        require_text(developer_session_id, "developer_session_id")
        self._bind_developer(actor_id)
        state.developer_session_id = developer_session_id.strip()
        write_task_files(self)
        self._save()
        self._event("developer_task", actor_id=actor_id, session_id=developer_session_id)
        return state

    def run_developer_backend(
        self: Engine,
        role: str,
        actor_id: str,
        developer_session_id: str,
    ) -> RunState:
        self._check_actor(role, actor_id)
        config = self._config()
        command = config.workflow.developer_command
        if command is None:
            raise PreconditionError(
                ["workflow.developer_command is null; run the developer agent manually and submit a report"]
            )
        self.materialize_developer_task(role, actor_id, developer_session_id)
        state = self.ensure()
        report_path = developer_dir(self.run_dir) / "report.json"
        env = {
            "CDW_REPO": str(self.repo),
            "CDW_RUN_DIR": str(self.run_dir),
            "CDW_DEMAND_ID": state.demand_id,
            "CDW_DEVELOPER_SESSION": developer_session_id,
            "CDW_DEVELOPER_TASK": str(developer_dir(self.run_dir) / "task.json"),
            "CDW_DEVELOPER_REPORT": str(report_path),
            "CDW_ACTOR": actor_id,
        }
        result = run_backend(command, env, self.repo, config.quality.command_timeout_seconds)
        self._event(
            "developer_backend",
            exit_code=result.exit_code,
            timed_out=result.timed_out,
            session_id=developer_session_id,
        )
        if not result.passed:
            state.implementation_ready = False
            state.failures.append(
                {
                    "at": utc_now(),
                    "stage": "IMPLEMENT",
                    "detail": "developer backend exited non-zero",
                }
            )
            self._save()
            raise WorkflowError("developer backend failed")
        if not report_path.is_file():
            raise PreconditionError(["developer backend did not write developer/report.json"])
        payload = json.loads(report_path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise PreconditionError(["developer report is not a JSON object"])
        return self.submit_developer_report(role, actor_id, payload, developer_session_id)

    def submit_developer_report(
        self: Engine,
        role: str,
        actor_id: str,
        payload: dict[str, object],
        developer_session_id: str | None = None,
    ) -> RunState:
        self._check_actor(role, actor_id)
        state = self.ensure()
        if state.status != "IMPLEMENT":
            raise InvalidTransition("developer reports are accepted only in IMPLEMENT")
        if role != "developer":
            raise PolicyError("only the developer role can submit an implementation report")
        self._bind_developer(actor_id)
        report = parse_report(payload)
        if developer_session_id:
            state.developer_session_id = developer_session_id.strip()
        elif report.developer_session_id:
            state.developer_session_id = report.developer_session_id
        problems = validate_report_against_repo(report, self.repo)
        if problems:
            raise PreconditionError(problems)
        report_path = developer_dir(self.run_dir) / "report.json"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        atomic_write(report_path, json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
        state.implementation_ready = True
        state.implement_hook_succeeded = False
        state.decisions.append(report.summary)
        self._save()
        self._event("developer_report", actor_id=actor_id, files=len(report.files_changed))
        return state

    def run_implement_hook(self: Engine, role: str, actor_id: str) -> RunState:
        self._check_actor(role, actor_id)
        state = self.ensure()
        config = self._config()
        if state.status != "IMPLEMENT":
            raise InvalidTransition("the implement hook runs only from IMPLEMENT")
        if role != "developer":
            raise PolicyError("only the developer role can run the implement hook")
        command = config.commands.implement
        if command is None:
            raise PreconditionError(
                ["commands.implement is null; the developer role must edit the repository"]
            )
        self._bind_developer(actor_id)
        record = run_command(
            self.repo,
            "implement",
            command,
            config.quality.command_timeout_seconds,
            self._commands_log(),
        )
        if record.passed:
            state.implementation_ready = True
            state.implement_hook_succeeded = True
            state.decisions.append("implement hook exited 0")
        else:
            state.implementation_ready = False
            state.failures.append(
                {"at": utc_now(), "stage": "IMPLEMENT", "detail": command_detail(record.name, record.exit_code)}
            )
        self._save()
        self._event("implement_hook", exit_code=record.exit_code, timed_out=record.timed_out)
        return state
