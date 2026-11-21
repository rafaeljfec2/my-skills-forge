"""Git branch and commit operations for the workflow engine."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

from connexto_workflow.engine_support import refuse_commit_path, require_text
from connexto_workflow.errors import InvalidTransition, PolicyError, PreconditionError, WorkflowError
from connexto_workflow.redact import contains_secret, redact
from connexto_workflow.state import RunState

if TYPE_CHECKING:
    from connexto_workflow.engine import Engine


class GitOpsMixin:
    """Mixin: git helpers and commit_work."""

    repo: Path
    run_dir: Path

    def _git(self: Engine, args: list[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *args],
            cwd=self.repo,
            capture_output=True,
            text=True,
            check=False,
        )

    def _current_branch(self: Engine) -> str:
        proc = self._git(["branch", "--show-current"])
        if proc.returncode != 0:
            raise WorkflowError(redact(proc.stderr.strip()) or "git branch failed")
        return proc.stdout.strip()

    def _commit_argv(self: Engine, message: str) -> list[str]:
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

    def _safe_repo_file(self: Engine, rel: str) -> Path:
        return refuse_commit_path(self.repo, rel)

    def _prepare_branch(self: Engine) -> None:
        config = self._config()
        state = self.ensure()
        if not config.git.isolated_branch:
            return
        if not (self.repo / ".git").exists():
            self._event("git_skipped", detail="not a git repository")
            return
        branch = state.git_branch or f"connexto/{state.demand_id}"
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

    def bind_work_branch(self: Engine, role: str, actor_id: str, branch: str) -> RunState:
        self._check_actor(role, actor_id)
        if role != "orchestrator":
            raise PolicyError("only the orchestrator can bind a work branch")
        state = self.ensure()
        if state.status not in {"PLAN", "IMPLEMENT"}:
            raise InvalidTransition("work branch is bound from PLAN or IMPLEMENT")
        require_text(branch, "branch")
        if branch == self._config().git.base_branch:
            raise PolicyError("work branch equals the base branch")
        if branch.startswith("-") or ".." in Path(branch).parts or "/" not in branch:
            raise PolicyError(f"refusing branch name: {branch}")
        state.git_branch = branch
        self._save()
        self._event("bind_branch", branch=branch, actor_id=actor_id)
        return state

    def commit_work(
        self: Engine,
        role: str,
        actor_id: str,
        message: str,
        paths: list[str],
    ) -> RunState:
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
        require_text(message, "message")
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
