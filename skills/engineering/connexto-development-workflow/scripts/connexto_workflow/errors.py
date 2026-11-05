"""Workflow errors. Messages name the failed gate; they do not include secrets."""

from __future__ import annotations


class WorkflowError(Exception):
    """Base error for a refused workflow operation."""


class ConfigError(WorkflowError):
    """Project configuration is missing, incomplete, or inconsistent."""


class InvalidTransition(WorkflowError):
    """The requested state edge is not defined for this reason."""


class PreconditionError(WorkflowError):
    """The edge exists, but required artifacts or flags are missing."""

    def __init__(self, problems: list[str]) -> None:
        self.problems = problems
        super().__init__("; ".join(problems))


class PolicyError(WorkflowError):
    """A security, approval, identity, or attempt-limit rule refused the action."""
