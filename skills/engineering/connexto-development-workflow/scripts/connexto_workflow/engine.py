"""Delivery state machine. Chat history is not the source of recovery."""

from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from connexto_workflow.commands import CommandRecord, run_command
from connexto_workflow.config import CONFIG_FILENAME, ProjectConfig, load_config
from connexto_workflow.developer import (
    developer_dir,
    parse_report,
    validate_report_against_repo,
    write_task_files,
)
from connexto_workflow.errors import (
    ConfigError,
    InvalidTransition,
    PolicyError,
    PreconditionError,
    WorkflowError,
)
from connexto_workflow.memory_sync import (
    execute_read,
    execute_write,
    prepare_body,
    record_sync_attempt,
    verify_read_body,
)
from connexto_workflow.model import (
    ACTIVE,
    BLOCKING_SEVERITIES,
    DEFAULT_RISK,
    DEMAND_TYPES,
    EDGE_ROLES,
    EDGES,
    INTERNAL_ONLY,
    NEXT_STEP,
    PROTECTED_ACTIONS,
    PUT_ROLES,
    PUTTABLE,
    RISK_RANK,
    TERMINAL,
)
from connexto_workflow.redact import contains_secret, redact
from connexto_workflow.reviewer import (
    JUDGE_SKILL,
    build_judge_bundle,
    parse_judge_output,
    write_findings_for_developer,
)
from connexto_workflow.review_schema import Finding, parse_review
from connexto_workflow.state import RunState, atomic_write, load_state
from connexto_workflow.backends import run_backend

_DEMAND_ID = re.compile(r"^[A-Z][A-Z0-9]*-\d{3,}$")
_ACTOR_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,40}$")
_PAGE = re.compile(r"^[A-Za-z0-9_./-]{3,200}$")
_ROLES = frozenset({"orchestrator", "researcher", "planner", "developer", "reviewer"})
_SEVERITIES = frozenset({"critical", "blocking", "important", "minor"})
_RETURN_TARGETS = frozenset({"IMPLEMENT", "PLAN"})
_RESET_REASONS = frozenset(
    {
        "validation_failed",
        "review_defect",
        "review_solution_failure",
        "scope_change",
        "inconsistent_plan",
    }
)
_RELEASE_KEYS = ("merge", "production_publish", "deploy")
_RELEASE_CLAIM = re.compile(
    r"(?i)\b(merged to main|merged to master|published to production|deployed to production)\b"
)
_SECRET_PATH_PARTS = frozenset({".connexto", ".env", ".git"})


@dataclass(frozen=True)
class Brief:
    demand_id: str
    demand_type: str
    problem: str
    desired_outcome: str
    scope: str
    success_criteria: tuple[str, ...]
    target_project: str
    constraints: tuple[str, ...] = ()
    risk: str | None = None


class Engine:
    """One demand directory under `<repo>/.connexto/runs/<id>`."""

    def __init__(self, repo: Path, demand_id: str) -> None:
        self.repo = repo.resolve()
        self.demand_id = demand_id
        self.run_dir = self.repo / ".connexto" / "runs" / demand_id
        self.state: RunState | None = None
        self.config: ProjectConfig | None = None

    def init_run(self, brief: Brief, config_path: Path | None = None) -> RunState:
        demand_type = _require_demand_type(brief.demand_type)
        demand_id = _require_demand_id(brief.demand_id, demand_type)
        if demand_id != self.demand_id:
            raise ConfigError("brief demand_id does not match the engine demand id")
        if self.run_dir.exists():
            raise WorkflowError(f"run already exists: {self.run_dir}")
        _require_text(brief.problem, "problem")
        _require_text(brief.desired_outcome, "desired_outcome")
        _require_text(brief.scope, "scope")
        _require_text(brief.target_project, "target_project")
        if not brief.success_criteria or any(not item.strip() for item in brief.success_criteria):
            raise ConfigError("success_criteria must contain at least one non-empty item")
        path = config_path or (self.repo / CONFIG_FILENAME)
        config = load_config(path)
        if brief.target_project != config.project.name:
            raise ConfigError("brief target_project does not match project.name")
        risk = effective_risk(demand_type, brief.risk)
        self.config = config
        now = _now()
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
        atomic_write(self.run_dir / "brief.md", _render_brief(brief, risk, now))
        self._save()
        self._event("init", risk=risk, project=config.project.name)
        return self.state

    def load(self) -> RunState:
        state_path = self.run_dir / "state.json"
        if not state_path.is_file():
            raise WorkflowError(f"no run state at {state_path}")
        _require_demand_id(self.demand_id, None)
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
            "next_step": NEXT_STEP[state.status],
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
        self._apply(to, role, actor_id, reason, internal=False)
        return self.ensure()

    def put_artifact(self, role: str, actor_id: str, name: str, body: str) -> RunState:
        self._check_actor(role, actor_id)
        state = self.ensure()
        if state.status in TERMINAL:
            raise InvalidTransition(f"run is {state.status}")
        if name not in PUTTABLE:
            raise PolicyError(f"{name} is not a hand-written artifact")
        if role not in PUT_ROLES[name]:
            raise PolicyError(f"role {role} cannot write {name}")
        if contains_secret(body):
            raise PolicyError(f"{name} contains credential-shaped text")
        if name == "research.md" and re.search(r"(?i)implemented:\s*yes", body):
            raise PolicyError("the researcher must not record that code was implemented")
        atomic_write(self.run_dir / name, body)
        self._event("artifact", name=name, actor_id=actor_id, role=role)
        return state

    def note_implementation(self, role: str, actor_id: str, summary: str) -> RunState:
        self._check_actor(role, actor_id)
        state = self.ensure()
        if state.status != "IMPLEMENT":
            raise InvalidTransition("implementation notes are accepted only in IMPLEMENT")
        if role != "developer":
            raise PolicyError("only the developer role can own the implementation")
        _require_text(summary, "summary")
        if contains_secret(summary):
            raise PolicyError("implementation note contains credential-shaped text")
        self._bind_developer(actor_id)
        state.decisions.append(summary.strip())
        self._save()
        self._event("implementation_note", actor_id=actor_id)
        return state

    def materialize_developer_task(self, role: str, actor_id: str, developer_session_id: str) -> RunState:
        self._check_actor(role, actor_id)
        state = self.ensure()
        if state.status != "IMPLEMENT":
            raise InvalidTransition("developer task materialization runs only in IMPLEMENT")
        if role != "developer":
            raise PolicyError("only the developer role can receive the task bundle")
        _require_text(developer_session_id, "developer_session_id")
        self._bind_developer(actor_id)
        state.developer_session_id = developer_session_id.strip()
        write_task_files(self)
        self._save()
        self._event("developer_task", actor_id=actor_id, session_id=developer_session_id)
        return state

    def run_developer_backend(self, role: str, actor_id: str, developer_session_id: str) -> RunState:
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
                    "at": _now(),
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
        self,
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

    def run_implement_hook(self, role: str, actor_id: str) -> RunState:
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
                {"at": _now(), "stage": "IMPLEMENT", "detail": _command_detail(record.name, record.exit_code)}
            )
        self._save()
        self._event("implement_hook", exit_code=record.exit_code, timed_out=record.timed_out)
        return state

    def run_validation(self, role: str, actor_id: str) -> RunState:
        self._check_actor(role, actor_id)
        state = self.ensure()
        if role not in {"developer", "orchestrator"}:
            raise PolicyError("only the developer or orchestrator can run validation")
        if state.status == "IMPLEMENT":
            self._apply("VALIDATE", role, actor_id, "implementation_ready", internal=True)
            state = self.ensure()
        elif state.status != "VALIDATE":
            raise InvalidTransition("validation runs from IMPLEMENT, or resumes from VALIDATE")
        if role == "developer" and actor_id != state.developer_id:
            raise PolicyError("this developer does not own the run")
        config = self._config()
        results = [
            run_command(
                self.repo,
                name,
                command,
                config.quality.command_timeout_seconds,
                self._commands_log(),
            )
            for name, command in config.required_commands()
        ]
        passed = all(record.passed for record in results)
        atomic_write(self.run_dir / "validation.md", _render_validation(self.demand_id, results))
        if passed:
            state.last_validation_passed = True
            self._save()
            self._apply("REVIEW", role, actor_id, "validation_passed", internal=True)
            return self.ensure()
        state.validate_failures += 1
        state.last_validation_passed = False
        state.implementation_ready = False
        state.failures.append(
            {
                "at": _now(),
                "stage": "VALIDATE",
                "detail": ", ".join(
                    _command_detail(record.name, record.exit_code) for record in results if not record.passed
                ),
            }
        )
        self._save()
        if state.validate_failures >= state.max_validate_attempts:
            self._apply("FAILED", role, actor_id, "attempts_exhausted", internal=True)
        else:
            self._apply("IMPLEMENT", role, actor_id, "validation_failed", internal=True)
        return self.ensure()

    def run_independent_judge(self, role: str, actor_id: str, reviewer_session_id: str) -> RunState:
        self._check_actor(role, actor_id)
        state = self.ensure()
        config = self._config()
        if state.status != "REVIEW":
            raise InvalidTransition("independent judge runs only in REVIEW")
        if role != "reviewer":
            raise PolicyError("only the reviewer role can run the judge")
        command = config.workflow.judge_command
        if command is None:
            raise PreconditionError(
                ["workflow.judge_command is null; invoke senior-code-review-judge manually and submit review.json"]
            )
        if state.developer_id is None:
            raise PreconditionError(["developer_id is not set"])
        if actor_id.casefold() == state.developer_id.casefold():
            raise PolicyError("the developer cannot review their own delivery")
        _require_text(reviewer_session_id, "reviewer_session_id")
        if state.developer_session_id and reviewer_session_id == state.developer_session_id:
            raise PolicyError("reviewer session must differ from developer session")
        next_round = state.review_round + 1
        if next_round > state.max_review_rounds:
            raise PolicyError("review round limit reached")
        build_judge_bundle(
            self.run_dir,
            self.repo,
            state,
            self.command_records(),
            reviewer_session_id,
            next_round,
        )
        output_path = self.run_dir / "review" / "judge-output.json"
        env = {
            "CDW_REPO": str(self.repo),
            "CDW_RUN_DIR": str(self.run_dir),
            "CDW_JUDGE_INPUT": str(self.run_dir / "review" / "judge-input" / "bundle.json"),
            "CDW_JUDGE_OUTPUT": str(output_path),
            "CDW_REVIEWER_SESSION": reviewer_session_id,
            "CDW_REVIEWER_ACTOR": actor_id,
            "CDW_REVIEW_ROUND": str(next_round),
            "CDW_JUDGE_SKILL": JUDGE_SKILL,
        }
        result = run_backend(command, env, self.repo, config.quality.command_timeout_seconds)
        self._event(
            "judge_backend",
            exit_code=result.exit_code,
            timed_out=result.timed_out,
            session_id=reviewer_session_id,
            round=next_round,
        )
        if not result.passed or not output_path.is_file():
            raise WorkflowError("judge backend failed or did not write judge-output.json")
        payload = json.loads(output_path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise PreconditionError(["judge output is not a JSON object"])
        verdict = parse_judge_output(payload)
        if verdict.reviewer_session_id != reviewer_session_id:
            raise PolicyError("judge output session id does not match request")
        if verdict.round_number != next_round:
            raise PolicyError("judge output round does not match request")
        state.review_round = next_round
        state.reviewer_session_id = reviewer_session_id
        review_payload = {
            "summary": verdict.summary,
            "findings": [item.__dict__ for item in verdict.findings],
            "verdict": verdict.verdict,
            "reviewer_session_id": reviewer_session_id,
            "developer_session_id": state.developer_session_id,
            "skill": verdict.skill,
            "round": next_round,
        }
        return self.submit_review(role, actor_id, review_payload, from_judge=True)

    def submit_review(
        self,
        role: str,
        actor_id: str,
        payload: dict[str, object],
        from_judge: bool = False,
    ) -> RunState:
        self._check_actor(role, actor_id)
        state = self.ensure()
        if state.status != "REVIEW":
            raise InvalidTransition("review is accepted only in REVIEW")
        if role != "reviewer":
            raise PolicyError("only the reviewer role can submit a review")
        if state.developer_id is None:
            raise PreconditionError(["developer_id is not set"])
        if actor_id.casefold() == state.developer_id.casefold():
            raise PolicyError("the developer cannot approve their own delivery")
        config = self._config()
        if config.workflow.judge_command and not from_judge:
            raise PolicyError(
                "workflow.judge_command is configured; run run-judge instead of manual review submission"
            )
        reviewer_session = payload.get("reviewer_session_id")
        if isinstance(reviewer_session, str) and reviewer_session.strip():
            if state.developer_session_id and reviewer_session == state.developer_session_id:
                raise PolicyError("reviewer session must differ from developer session")
            state.reviewer_session_id = reviewer_session.strip()
        summary, findings = parse_review(payload)
        if contains_secret(summary) or any(contains_secret(item.rationale) for item in findings):
            raise PolicyError("review contains credential-shaped text")
        blocking = [item for item in findings if item.severity in BLOCKING_SEVERITIES[state.risk]]
        verdict = payload.get("verdict")
        if isinstance(verdict, str) and verdict.strip().upper() in {"REJECTED", "INCOMPLETE"}:
            blocking = findings or blocking
        state.reviewer_id = actor_id
        review_body = {
            "reviewer": actor_id,
            "developer": state.developer_id,
            "summary": summary,
            "findings": [item.__dict__ for item in findings],
            "reviewer_session_id": state.reviewer_session_id,
            "developer_session_id": state.developer_session_id,
            "round": state.review_round,
            "skill": payload.get("skill", JUDGE_SKILL if from_judge else None),
            "verdict": verdict,
        }
        atomic_write(
            self.run_dir / "review.json",
            json.dumps(review_body, indent=2, ensure_ascii=False) + "\n",
        )
        atomic_write(self.run_dir / "review.md", _render_review(self.demand_id, actor_id, summary, findings))
        self._save()
        if not blocking:
            self._apply("DELIVERY", role, actor_id, "review_clear", internal=True)
            return self.ensure()
        write_findings_for_developer(self.run_dir, blocking)
        destination = "PLAN" if any(item.return_to == "PLAN" for item in blocking) else "IMPLEMENT"
        reason = "review_solution_failure" if destination == "PLAN" else "review_defect"
        if state.review_round >= state.max_review_rounds and destination == "IMPLEMENT":
            raise PolicyError("review round limit reached with blocking findings")
        state.last_validation_passed = False
        state.implementation_ready = False
        self._save()
        self._apply(destination, role, actor_id, reason, internal=True)
        return self.ensure()

    def compose_delivery(self, role: str, actor_id: str, sections: dict[str, str]) -> RunState:
        self._check_actor(role, actor_id)
        state = self.ensure()
        if state.status != "DELIVERY":
            raise InvalidTransition("delivery is composed only in DELIVERY")
        if role != "orchestrator":
            raise PolicyError("only the orchestrator can compose delivery")
        required = ("problem_solved", "solution", "files_changed", "limitations", "follow_ups")
        missing = [key for key in required if not sections.get(key, "").strip()]
        if missing:
            raise PreconditionError([f"delivery section {key} is empty" for key in missing])
        if any(contains_secret(value) for value in sections.values()):
            raise PolicyError("delivery contains credential-shaped text")
        text = _render_delivery(self.demand_id, state, sections, self._command_records(), self._review_summary())
        if _RELEASE_CLAIM.search(text):
            raise PolicyError("delivery claims a merge, production publish, or deploy that was not authorized")
        atomic_write(self.run_dir / "delivery.md", text)
        state.delivery_ready = True
        self._save()
        self._event("delivery_composed", actor_id=actor_id)
        return state

    def memory_payload(self) -> dict[str, object]:
        self.ensure()
        path = self.run_dir / "memory" / "payload.json"
        if not path.is_file():
            self._write_memory_payload()
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise WorkflowError("memory payload is not an object")
        return data

    def ack_memory(self, role: str, actor_id: str, page: str) -> RunState:
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
        if not _PAGE.match(page) or ".." in page.split("/"):
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

    def sync_memory(self, role: str, actor_id: str) -> RunState:
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

    def skip_memory(self, role: str, actor_id: str, reason: str) -> RunState:
        self._check_actor(role, actor_id)
        state = self.ensure()
        if self._config().memory.enabled:
            raise PolicyError("memory is enabled; ack a page instead of skipping")
        if state.status != "MEMORY":
            raise InvalidTransition("memory skip is accepted only in MEMORY")
        if role != "orchestrator":
            raise PolicyError("only the orchestrator can skip memory")
        _require_text(reason, "reason")
        state.memory_skipped_reason = reason.strip()
        self._save()
        self._apply("DONE", role, actor_id, "memory_skipped", internal=True)
        return self.ensure()

    def approve(self, role: str, actor_id: str, action: str) -> RunState:
        self._check_actor(role, actor_id)
        state = self.ensure()
        if state.status != "WAITING_APPROVAL":
            raise InvalidTransition("there is nothing waiting for approval")
        if role != "orchestrator":
            raise PolicyError("only the orchestrator can record an approval")
        if actor_id == state.pending_actor:
            raise PolicyError("the actor who requested approval cannot approve it")
        if action != state.pending_action:
            raise PolicyError("approval action does not match the pending action")
        destination = state.pending_to
        reason = state.pending_reason
        pending_role = state.pending_role or "orchestrator"
        pending_actor = state.pending_actor or actor_id
        resume = state.resume_status
        if action not in state.approvals:
            state.approvals.append(action)
        state.pending_to = None
        state.pending_reason = None
        state.pending_role = None
        state.pending_actor = None
        state.pending_action = None
        state.resume_status = None
        state.status = resume or state.status
        self._save()
        self._event("approved", action=action, actor_id=actor_id)
        if destination is None or reason is None:
            return state
        self._apply(destination, pending_role, pending_actor, reason, internal=False)
        return self.ensure()

    def request_protected(self, role: str, actor_id: str, action: str) -> RunState:
        self._check_actor(role, actor_id)
        state = self.ensure()
        if state.status not in ACTIVE:
            raise InvalidTransition("protected actions are requested from an active state")
        if role != "orchestrator":
            raise PolicyError("only the orchestrator can request a protected action")
        if action not in PROTECTED_ACTIONS:
            raise PolicyError(f"unknown protected action: {action}")
        token = f"protected:{action}"
        if token in state.approvals:
            self._event("protected_already_approved", action=action)
            return state
        self._park(None, "risk_not_authorized", role, actor_id, token)
        return self.ensure()

    def block(self, role: str, actor_id: str, dependency: str) -> RunState:
        self._check_actor(role, actor_id)
        state = self.ensure()
        if state.status not in ACTIVE:
            raise InvalidTransition("only an active run can become BLOCKED")
        if role != "orchestrator":
            raise PolicyError("only the orchestrator can block a run")
        _require_text(dependency, "dependency")
        state.blocked_dependency = dependency.strip()
        state.resume_status = state.status
        state.status = "BLOCKED"
        state.updated_at = _now()
        self._save()
        self._event("blocked", dependency=dependency.strip(), actor_id=actor_id)
        return state

    def unblock(self, role: str, actor_id: str) -> RunState:
        self._check_actor(role, actor_id)
        state = self.ensure()
        if state.status != "BLOCKED":
            raise InvalidTransition("run is not BLOCKED")
        if role != "orchestrator":
            raise PolicyError("only the orchestrator can unblock a run")
        if not state.resume_status:
            raise PreconditionError(["resume_status is missing"])
        state.status = state.resume_status
        state.resume_status = None
        state.blocked_dependency = None
        state.updated_at = _now()
        self._save()
        self._event("unblocked", actor_id=actor_id)
        return state

    def fail(self, role: str, actor_id: str, detail: str) -> RunState:
        return self._terminal_from_operator("FAILED", role, actor_id, detail)

    def cancel(self, role: str, actor_id: str, detail: str) -> RunState:
        return self._terminal_from_operator("CANCELLED", role, actor_id, detail)

    def commit_work(self, role: str, actor_id: str, message: str, paths: list[str]) -> RunState:
        self._check_actor(role, actor_id)
        state = self.ensure()
        config = self._config()
        if not config.git.allow_commit:
            raise PolicyError("git.allow_commit is false")
        if role not in {"developer", "orchestrator"}:
            raise PolicyError("only the developer or orchestrator can commit")
        if role == "developer":
            self._bind_developer(actor_id)
        if state.status not in {"IMPLEMENT", "REVIEW"}:
            raise InvalidTransition("commits are accepted in IMPLEMENT or REVIEW")
        _require_text(message, "message")
        if contains_secret(message):
            raise PolicyError("commit message contains credential-shaped text")
        if not paths:
            raise PreconditionError(["commit paths are empty"])
        current = self._current_branch()
        if current == config.git.base_branch:
            raise PolicyError("refusing commit on the base branch")
        safe_paths: list[str] = []
        for rel in paths:
            path = self._safe_repo_file(rel)
            text = path.read_text(encoding="utf-8", errors="replace")
            if contains_secret(text):
                raise PolicyError(f"refusing to commit secret-shaped content in {rel}")
            safe_paths.append(rel)
        add = self._git(["add", "--", *safe_paths])
        if add.returncode != 0:
            raise WorkflowError(redact(add.stderr.strip()) or "git add failed")
        commit = subprocess.run(
            self._commit_argv(message.strip()),
            cwd=self.repo,
            capture_output=True,
            text=True,
            check=False,
        )
        if commit.returncode != 0:
            raise WorkflowError(redact(commit.stderr.strip()) or "git commit failed")
        head = self._git(["rev-parse", "HEAD"])
        state.git_commit = head.stdout.strip()
        state.git_branch = current
        self._save()
        self._event("commit", commit=state.git_commit, branch=current, actor_id=actor_id)
        return state

    def _terminal_from_operator(self, status: str, role: str, actor_id: str, detail: str) -> RunState:
        self._check_actor(role, actor_id)
        state = self.ensure()
        if state.status in TERMINAL or state.status == "PENDING":
            raise InvalidTransition(f"cannot move {state.status} to {status}")
        if role != "orchestrator":
            raise PolicyError("only the orchestrator can fail or cancel a run")
        _require_text(detail, "detail")
        state.failures.append({"at": _now(), "stage": state.status, "detail": detail.strip()})
        state.status = status
        state.updated_at = _now()
        self._save()
        self._event(status.lower(), detail=detail.strip(), actor_id=actor_id)
        return state

    def _apply(self, to: str, role: str, actor_id: str, reason: str, internal: bool) -> None:
        state = self.ensure()
        source = state.status
        edge = (source, to)
        if edge not in EDGES or reason not in EDGES[edge]:
            raise InvalidTransition(f"{source} -> {to} ({reason}) is not defined")
        if edge in INTERNAL_ONLY and not internal:
            raise InvalidTransition(f"{source} -> {to} is gated by an engine operation")
        if role not in EDGE_ROLES[edge]:
            raise PolicyError(f"role {role} cannot take {source} -> {to}")
        problems = self._preconditions(source, to, reason)
        if problems:
            raise PreconditionError(problems)
        if not internal and source == "INTAKE" and to == "RESEARCH" and state.risk == "HIGH":
            if "start_high_risk" not in state.approvals:
                self._park(to, reason, role, actor_id, "start_high_risk")
                return
        if to == "IMPLEMENT":
            self._prepare_branch()
        if to in {"IMPLEMENT", "PLAN"} and reason in _RESET_REASONS:
            state.last_validation_passed = False
            state.implementation_ready = False
        state.status = to
        state.updated_at = _now()
        if to == "MEMORY":
            self._write_memory_payload()
        self._save()
        self._event("transition", source=source, dest=to, reason=reason, role=role, actor_id=actor_id)

    def _preconditions(self, source: str, to: str, reason: str) -> list[str]:
        state = self.ensure()
        problems: list[str] = []
        if (source, to) == ("INTAKE", "RESEARCH"):
            brief = self._read_optional("brief.md")
            if f"Demand: {state.demand_id}" not in brief:
                problems.append("brief.md is missing the demand id")
            for heading in ("## Problem", "## Desired outcome", "## Success criteria"):
                if heading not in brief:
                    problems.append(f"brief.md is missing {heading}")
            if not (self.run_dir / "project.snapshot.json").is_file():
                problems.append("project snapshot is missing")
        if (source, to) == ("RESEARCH", "PLAN"):
            body = self._read_optional("research.md")
            for heading in ("## Facts", "## Hypotheses", "## Gaps", "## Evidence"):
                if heading not in body:
                    problems.append(f"research.md is missing {heading}")
            if not re.search(r"(?m)^Implemented: no\s*$", body):
                problems.append("research.md must contain the line 'Implemented: no'")
        if (source, to) == ("PLAN", "IMPLEMENT") and reason == "plan_accepted":
            spec = self._read_optional("spec.md")
            plan = self._read_optional("plan.md")
            tasks = self._read_optional("tasks.md")
            if "## Behavior" not in spec:
                problems.append("spec.md is missing ## Behavior")
            if "## Acceptance criteria" not in plan:
                problems.append("plan.md is missing ## Acceptance criteria")
            if "- [ ]" not in tasks:
                problems.append("tasks.md has no open task")
        if (source, to) == ("IMPLEMENT", "VALIDATE"):
            report_path = developer_dir(self.run_dir) / "report.json"
            if not state.implementation_ready:
                problems.append("implementation is not ready")
            if not state.developer_id:
                problems.append("developer_id is not set")
            if not state.implement_hook_succeeded and not report_path.is_file():
                problems.append("developer/report.json or a successful implement hook is required")
        if (source, to) == ("VALIDATE", "REVIEW") and not state.last_validation_passed:
            problems.append("the latest validation did not pass")
        if (source, to) == ("VALIDATE", "IMPLEMENT") and reason == "validation_failed":
            if state.last_validation_passed:
                problems.append("validation passed; refusing the failure return")
            if state.validate_failures < 1 or state.validate_failures >= state.max_validate_attempts:
                problems.append("failure return is outside the attempt window")
        if (source, to) == ("VALIDATE", "FAILED") and state.validate_failures < state.max_validate_attempts:
            problems.append("attempts are not exhausted")
        if (source, to) == ("REVIEW", "DELIVERY"):
            if state.reviewer_id is None or state.developer_id is None:
                problems.append("reviewer and developer must both be set")
            elif state.reviewer_id.casefold() == state.developer_id.casefold():
                problems.append("reviewer and developer are the same actor")
            if not (self.run_dir / "review.json").is_file():
                problems.append("review.json is missing")
        if (source, to) == ("DELIVERY", "MEMORY") and not state.delivery_ready:
            problems.append("delivery.md has not been composed")
        if (source, to) == ("MEMORY", "DONE") and reason == "memory_recorded":
            if not self._config().memory.enabled:
                problems.append("memory is disabled")
            config = self._config()
            if config.workflow.memory_write_command:
                if state.memory_remote_status != "confirmed":
                    problems.append("remote memory is not confirmed")
                if not state.memory_ack_page:
                    problems.append("memory page path is missing after sync")
            elif not state.memory_ack_page:
                problems.append("memory page has not been acked")
        if (source, to) == ("MEMORY", "DONE") and reason == "memory_skipped":
            if self._config().memory.enabled:
                problems.append("memory is enabled")
            if not state.memory_skipped_reason:
                problems.append("memory skip reason is missing")
        return problems

    def _park(
        self,
        to: str | None,
        reason: str,
        role: str,
        actor_id: str,
        action: str,
    ) -> None:
        state = self.ensure()
        state.resume_status = state.status
        state.pending_to = to
        state.pending_reason = reason
        state.pending_role = role
        state.pending_actor = actor_id
        state.pending_action = action
        state.status = "WAITING_APPROVAL"
        state.updated_at = _now()
        self._save()
        self._event("waiting_approval", action=action, dest=to, actor_id=actor_id)

    def _prepare_branch(self) -> None:
        config = self._config()
        state = self.ensure()
        if not config.git.isolated_branch:
            return
        if not (self.repo / ".git").exists():
            self._event("git_skipped", detail="not a git repository")
            return
        branch = f"connexto/{state.demand_id}"
        if branch == config.git.base_branch:
            raise PolicyError("work branch equals the base branch")
        current = self._current_branch()
        if current == branch:
            state.git_branch = branch
            return
        verify = self._git(["rev-parse", "--verify", "--quiet", branch])
        args = ["checkout", branch] if verify.returncode == 0 else ["checkout", "-b", branch]
        checkout = self._git(args)
        if checkout.returncode != 0:
            detail = redact(checkout.stderr.strip()) or "git checkout failed"
            raise WorkflowError(detail)
        state.git_branch = branch

    def _bind_developer(self, actor_id: str) -> None:
        state = self.ensure()
        if state.developer_id is None:
            state.developer_id = actor_id
            return
        if state.developer_id != actor_id:
            raise PolicyError("a different developer already owns this run")

    def _write_memory_payload(self) -> None:
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
            "artifacts": sorted(
                path.name for path in self.run_dir.iterdir() if path.is_file()
            ),
            "run_dir": str(self.run_dir),
        }
        atomic_write(
            self.run_dir / "memory" / "payload.json",
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        )

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
        self.state.updated_at = _now()
        atomic_write(self.run_dir / "state.json", self.state.to_json())

    def _event(self, kind: str, **fields: object) -> None:
        state = self.ensure()
        payload: dict[str, object] = {
            "at": _now(),
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
        if role not in _ROLES:
            raise PolicyError(f"unknown role: {role}")
        if not _ACTOR_ID.match(actor_id):
            raise PolicyError("actor id is invalid")

    def _git(self, args: list[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *args],
            cwd=self.repo,
            capture_output=True,
            text=True,
            check=False,
        )

    def _current_branch(self) -> str:
        proc = self._git(["branch", "--show-current"])
        if proc.returncode != 0:
            raise WorkflowError(redact(proc.stderr.strip()) or "git branch failed")
        return proc.stdout.strip()

    def _commit_argv(self, message: str) -> list[str]:
        email = self._git(["config", "--get", "user.email"])
        if email.returncode == 0 and email.stdout.strip():
            return ["git", "commit", "-m", message]
        return [
            "git",
            "-c",
            "user.email=connexto-workflow@localhost",
            "-c",
            "user.name=Connexto Workflow",
            "commit",
            "-m",
            message,
        ]

    def _safe_repo_file(self, rel: str) -> Path:
        if rel.startswith("/") or "\\" in rel:
            raise PolicyError(f"refusing path: {rel}")
        parts = Path(rel).parts
        if ".." in parts or any(part in _SECRET_PATH_PARTS or part.startswith(".env") for part in parts):
            raise PolicyError(f"refusing path: {rel}")
        path = (self.repo / rel).resolve()
        if not _is_inside(path, self.repo) or not path.is_file():
            raise PolicyError(f"refusing path: {rel}")
        if path.suffix.lower() in {".pem", ".key"} or path.name.lower() in {"credentials.json", "id_rsa", "id_rsa.pub"}:
            raise PolicyError(f"refusing secret-shaped path: {rel}")
        if "secret" in path.name.lower():
            raise PolicyError(f"refusing secret-shaped path: {rel}")
        return path


def effective_risk(demand_type: str, explicit: str | None) -> str:
    base = DEFAULT_RISK[demand_type]
    if explicit is None:
        return base
    if explicit not in RISK_RANK:
        raise ConfigError(f"unknown risk: {explicit}")
    if RISK_RANK[explicit] < RISK_RANK[base]:
        raise PolicyError(f"cannot lower {demand_type} risk from {base} to {explicit}")
    return explicit


def _require_demand_type(demand_type: str) -> str:
    if demand_type not in DEMAND_TYPES:
        raise ConfigError(f"unknown demand type: {demand_type}")
    return demand_type


def _require_demand_id(demand_id: str, demand_type: str | None) -> str:
    if not _DEMAND_ID.match(demand_id):
        raise ConfigError("demand id must look like FEAT-001")
    if demand_type is not None:
        prefix = DEMAND_TYPES[demand_type]
        if not demand_id.startswith(prefix + "-"):
            raise ConfigError(f"{demand_type} ids must start with {prefix}-")
    return demand_id


def _require_text(value: str, label: str) -> None:
    if not value.strip():
        raise ConfigError(f"{label} is empty")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _command_detail(name: str, exit_code: int | None) -> str:
    rendered = "timeout" if exit_code is None else str(exit_code)
    return f"{name} exit {rendered}"


def _render_brief(brief: Brief, risk: str, now: str) -> str:
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


def _render_validation(demand_id: str, results: list[CommandRecord]) -> str:
    lines = [f"# Validation\n", f"- Demand: {demand_id}\n", "\n## Commands\n"]
    for result in results:
        rendered = "timeout" if result.timed_out else str(result.exit_code)
        lines.append(f"- {result.name}: exit {rendered} argv `{shlex_join(result.argv)}`\n")
    return "".join(lines)


def _render_review(demand_id: str, reviewer: str, summary: str, findings: list[Finding]) -> str:
    rows = ["# Review\n", f"- Demand: {demand_id}\n", f"- Reviewer: {reviewer}\n", "\n## Summary\n", summary, "\n\n## Findings\n"]
    if not findings:
        rows.append("- none\n")
    for item in findings:
        rows.append(
            f"- {item.severity} `{item.file}` ({item.location}): {item.rationale} → {item.return_to}\n"
        )
    return "".join(rows)


def _render_delivery(
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
    release = [f"- {key}: not performed" for key in _RELEASE_KEYS]
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


def _is_inside(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def shlex_join(argv: object) -> str:
    if not isinstance(argv, list):
        return ""
    return " ".join(str(part) for part in argv)
