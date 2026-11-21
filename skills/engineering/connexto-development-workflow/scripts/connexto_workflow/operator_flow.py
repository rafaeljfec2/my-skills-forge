"""Orchestrator artifacts, validation, delivery, approvals, and terminal states."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from connexto_workflow.commands import run_command
from connexto_workflow.engine_support import RELEASE_CLAIM, command_detail, require_text, utc_now
from connexto_workflow.errors import InvalidTransition, PolicyError, PreconditionError
from connexto_workflow.model import ACTIVE, PROTECTED_ACTIONS, PUT_ROLES, PUTTABLE, TERMINAL
from connexto_workflow.redact import contains_secret
from connexto_workflow.render import render_delivery, render_validation
from connexto_workflow.state import RunState, atomic_write
from connexto_workflow.transition_ops import apply_transition, park_run

if TYPE_CHECKING:
    from connexto_workflow.engine import Engine


class OperatorFlowMixin:
    def put_artifact(self: Engine, role: str, actor_id: str, name: str, body: str) -> RunState:
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

    def note_implementation(self: Engine, role: str, actor_id: str, summary: str) -> RunState:
        self._check_actor(role, actor_id)
        state = self.ensure()
        if state.status != "IMPLEMENT":
            raise InvalidTransition("implementation notes are accepted only in IMPLEMENT")
        if role != "developer":
            raise PolicyError("only the developer role can own the implementation")
        require_text(summary, "summary")
        if contains_secret(summary):
            raise PolicyError("implementation note contains credential-shaped text")
        self._bind_developer(actor_id)
        state.decisions.append(summary.strip())
        self._save()
        self._event("implementation_note", actor_id=actor_id)
        return state

    def run_validation(self: Engine, role: str, actor_id: str) -> RunState:
        self._check_actor(role, actor_id)
        state = self.ensure()
        if role not in {"developer", "orchestrator", "validator"}:
            raise PolicyError("only the developer, orchestrator, or validator can run validation")
        if role == "validator" and (
            state.developer_id is None or actor_id.casefold() == state.developer_id.casefold()
        ):
            raise PolicyError("validator must differ from the developer")
        if state.status == "IMPLEMENT":
            apply_transition(self, "VALIDATE", role, actor_id, "implementation_ready", internal=True)
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
        atomic_write(self.run_dir / "validation.md", render_validation(self.demand_id, results))
        if passed:
            state.last_validation_passed = True
            self._save()
            apply_transition(self, "REVIEW", role, actor_id, "validation_passed", internal=True)
            return self.ensure()
        state.validate_failures += 1
        state.last_validation_passed = False
        state.implementation_ready = False
        state.failures.append(
            {
                "at": utc_now(),
                "stage": "VALIDATE",
                "detail": ", ".join(
                    command_detail(record.name, record.exit_code) for record in results if not record.passed
                ),
            }
        )
        self._save()
        if state.validate_failures >= state.max_validate_attempts:
            apply_transition(self, "FAILED", role, actor_id, "attempts_exhausted", internal=True)
        else:
            apply_transition(self, "IMPLEMENT", role, actor_id, "validation_failed", internal=True)
        return self.ensure()

    def compose_delivery(self: Engine, role: str, actor_id: str, sections: dict[str, str]) -> RunState:
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
        text = render_delivery(
            self.demand_id, state, sections, self._command_records(), self._review_summary()
        )
        if RELEASE_CLAIM.search(text):
            raise PolicyError("delivery claims a merge, production publish, or deploy that was not authorized")
        atomic_write(self.run_dir / "delivery.md", text)
        state.delivery_ready = True
        self._save()
        self._event("delivery_composed", actor_id=actor_id)
        return state

    def approve(self: Engine, role: str, actor_id: str, action: str) -> RunState:
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
        apply_transition(self, destination, pending_role, pending_actor, reason, internal=False)
        return self.ensure()

    def request_protected(self: Engine, role: str, actor_id: str, action: str) -> RunState:
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
        park_run(self, None, "risk_not_authorized", role, actor_id, token)
        return self.ensure()

    def block(self: Engine, role: str, actor_id: str, dependency: str) -> RunState:
        self._check_actor(role, actor_id)
        state = self.ensure()
        if state.status not in ACTIVE:
            raise InvalidTransition("only an active run can become BLOCKED")
        if role != "orchestrator":
            raise PolicyError("only the orchestrator can block a run")
        require_text(dependency, "dependency")
        state.blocked_dependency = dependency.strip()
        state.resume_status = state.status
        state.status = "BLOCKED"
        state.updated_at = utc_now()
        self._save()
        self._event("blocked", dependency=dependency.strip(), actor_id=actor_id)
        return state

    def unblock(self: Engine, role: str, actor_id: str) -> RunState:
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
        state.updated_at = utc_now()
        self._save()
        self._event("unblocked", actor_id=actor_id)
        return state

    def fail(self: Engine, role: str, actor_id: str, detail: str) -> RunState:
        return self._terminal_from_operator("FAILED", role, actor_id, detail)

    def cancel(self: Engine, role: str, actor_id: str, detail: str) -> RunState:
        return self._terminal_from_operator("CANCELLED", role, actor_id, detail)

    def _terminal_from_operator(self: Engine, status: str, role: str, actor_id: str, detail: str) -> RunState:
        self._check_actor(role, actor_id)
        state = self.ensure()
        if state.status in TERMINAL or state.status == "PENDING":
            raise InvalidTransition(f"cannot move {state.status} to {status}")
        if role != "orchestrator":
            raise PolicyError("only the orchestrator can fail or cancel a run")
        require_text(detail, "detail")
        state.failures.append({"at": utc_now(), "stage": state.status, "detail": detail.strip()})
        state.status = status
        state.updated_at = utc_now()
        self._save()
        self._event(status.lower(), detail=detail.strip(), actor_id=actor_id)
        return state
