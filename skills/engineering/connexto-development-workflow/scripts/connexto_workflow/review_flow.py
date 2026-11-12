"""Independent judge and review submission."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from connexto_workflow.backends import run_backend
from connexto_workflow.errors import InvalidTransition, PolicyError, PreconditionError, WorkflowError
from connexto_workflow.model import BLOCKING_SEVERITIES
from connexto_workflow.redact import contains_secret
from connexto_workflow.engine_support import require_text
from connexto_workflow.render import render_review
from connexto_workflow.reviewer import (
    JUDGE_SKILL,
    build_judge_bundle,
    parse_judge_output,
    write_findings_for_developer,
)
from connexto_workflow.review_schema import parse_review
from connexto_workflow.state import RunState, atomic_write

if TYPE_CHECKING:
    from connexto_workflow.engine import Engine


class ReviewFlowMixin:
    def run_independent_judge(
        self: Engine,
        role: str,
        actor_id: str,
        reviewer_session_id: str,
    ) -> RunState:
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
        require_text(reviewer_session_id, "reviewer_session_id")
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
        self: Engine,
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
        atomic_write(self.run_dir / "review.md", render_review(self.demand_id, actor_id, summary, findings))
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
