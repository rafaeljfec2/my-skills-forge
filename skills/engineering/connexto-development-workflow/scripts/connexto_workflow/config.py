"""Strict project adapter. Missing commands stay missing; nothing is inferred."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from connexto_workflow.errors import ConfigError
from connexto_workflow.redact import contains_secret

CONFIG_FILENAME = "connexto.project.json"

_TOP_LEVEL = ("project", "commands", "quality", "git", "memory", "workflow")
_PROJECT_KEYS = ("name", "language", "framework")
_COMMAND_KEYS = ("install", "test", "lint", "typecheck", "build", "implement")
_QUALITY_KEYS = (
    "require_tests",
    "require_lint",
    "require_typecheck",
    "require_build",
    "max_validate_attempts",
    "command_timeout_seconds",
)
_GIT_KEYS = ("base_branch", "isolated_branch", "allow_commit")
_MEMORY_KEYS = ("enabled", "workspace", "project")
_WORKFLOW_KEYS = (
    "max_review_rounds",
    "developer_command",
    "judge_command",
    "memory_write_command",
    "memory_read_command",
)
_REQUIREMENT_COMMAND = {
    "require_tests": "test",
    "require_lint": "lint",
    "require_typecheck": "typecheck",
    "require_build": "build",
}


@dataclass(frozen=True)
class ProjectInfo:
    name: str
    language: str | None
    framework: str | None


@dataclass(frozen=True)
class CommandSet:
    install: str | None
    test: str | None
    lint: str | None
    typecheck: str | None
    build: str | None
    implement: str | None

    def as_dict(self) -> dict[str, str | None]:
        return {
            "install": self.install,
            "test": self.test,
            "lint": self.lint,
            "typecheck": self.typecheck,
            "build": self.build,
            "implement": self.implement,
        }


@dataclass(frozen=True)
class QualityGate:
    require_tests: bool
    require_lint: bool
    require_typecheck: bool
    require_build: bool
    max_validate_attempts: int
    command_timeout_seconds: int


@dataclass(frozen=True)
class GitPolicy:
    base_branch: str
    isolated_branch: bool
    allow_commit: bool


@dataclass(frozen=True)
class WorkflowPolicy:
    max_review_rounds: int
    developer_command: str | None
    judge_command: str | None
    memory_write_command: str | None
    memory_read_command: str | None


@dataclass(frozen=True)
class MemoryPolicy:
    enabled: bool
    workspace: str | None
    project: str | None


@dataclass(frozen=True)
class ProjectConfig:
    project: ProjectInfo
    commands: CommandSet
    quality: QualityGate
    git: GitPolicy
    memory: MemoryPolicy
    workflow: WorkflowPolicy

    def required_commands(self) -> list[tuple[str, str]]:
        """Return (gate name, argv string) for every enabled quality command."""
        mapping = {
            "test": (self.quality.require_tests, self.commands.test),
            "lint": (self.quality.require_lint, self.commands.lint),
            "typecheck": (self.quality.require_typecheck, self.commands.typecheck),
            "build": (self.quality.require_build, self.commands.build),
        }
        required: list[tuple[str, str]] = []
        for name, (enabled, command) in mapping.items():
            if enabled:
                if command is None:
                    raise ConfigError(f"quality requires {name}, but commands.{name} is null")
                required.append((name, command))
        return required


def load_config(path: Path) -> ProjectConfig:
    if not path.is_file():
        raise ConfigError(
            f"missing {path.name} at {path}. "
            "The workflow does not assume a language, framework, or command."
        )
    text = path.read_text(encoding="utf-8")
    if contains_secret(text):
        raise ConfigError(f"{path.name} contains credential-shaped text; remove it before loading")
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ConfigError(f"{path.name} is not JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ConfigError(f"{path.name} must be a JSON object")
    return parse_config(data)


def parse_config(data: dict[str, object]) -> ProjectConfig:
    _exact_keys(data, _TOP_LEVEL, "config")
    project = _object(data["project"], "project")
    commands = _object(data["commands"], "commands")
    quality = _object(data["quality"], "quality")
    git = _object(data["git"], "git")
    memory = _object(data["memory"], "memory")
    workflow = _object(data["workflow"], "workflow")
    _exact_keys(project, _PROJECT_KEYS, "project")
    _exact_keys(commands, _COMMAND_KEYS, "commands")
    _exact_keys(quality, _QUALITY_KEYS, "quality")
    _exact_keys(git, _GIT_KEYS, "git")
    _exact_keys(memory, _MEMORY_KEYS, "memory")
    _exact_keys(workflow, _WORKFLOW_KEYS, "workflow")

    name = _nonempty_string(project["name"], "project.name")
    language = _optional_string(project["language"], "project.language")
    framework = _optional_string(project["framework"], "project.framework")
    command_set = CommandSet(
        install=_optional_command(commands["install"], "commands.install"),
        test=_optional_command(commands["test"], "commands.test"),
        lint=_optional_command(commands["lint"], "commands.lint"),
        typecheck=_optional_command(commands["typecheck"], "commands.typecheck"),
        build=_optional_command(commands["build"], "commands.build"),
        implement=_optional_command(commands["implement"], "commands.implement"),
    )
    attempts = _bounded_int(quality["max_validate_attempts"], "quality.max_validate_attempts", 1, 20)
    timeout = _bounded_int(
        quality["command_timeout_seconds"],
        "quality.command_timeout_seconds",
        1,
        3600,
    )
    gate = QualityGate(
        require_tests=_bool(quality["require_tests"], "quality.require_tests"),
        require_lint=_bool(quality["require_lint"], "quality.require_lint"),
        require_typecheck=_bool(quality["require_typecheck"], "quality.require_typecheck"),
        require_build=_bool(quality["require_build"], "quality.require_build"),
        max_validate_attempts=attempts,
        command_timeout_seconds=timeout,
    )
    if not any((gate.require_tests, gate.require_lint, gate.require_typecheck, gate.require_build)):
        raise ConfigError("quality must require at least one of test, lint, typecheck, or build")
    for flag, command_name in _REQUIREMENT_COMMAND.items():
        if getattr(gate, flag) and getattr(command_set, command_name) is None:
            raise ConfigError(f"quality.{flag} is true but commands.{command_name} is null")

    memory_enabled = _bool(memory["enabled"], "memory.enabled")
    workspace = _optional_string(memory["workspace"], "memory.workspace")
    memory_project = _optional_string(memory["project"], "memory.project")
    if memory_enabled and (workspace is None or memory_project is None):
        raise ConfigError("memory.enabled requires memory.workspace and memory.project")

    max_review_rounds = _bounded_int(
        workflow["max_review_rounds"],
        "workflow.max_review_rounds",
        1,
        20,
    )
    developer_command = _optional_command(workflow["developer_command"], "workflow.developer_command")
    judge_command = _optional_command(workflow["judge_command"], "workflow.judge_command")
    memory_write_command = _optional_command(
        workflow["memory_write_command"],
        "workflow.memory_write_command",
    )
    memory_read_command = _optional_command(
        workflow["memory_read_command"],
        "workflow.memory_read_command",
    )
    if memory_write_command and not memory_read_command:
        raise ConfigError("workflow.memory_write_command requires workflow.memory_read_command")
    if memory_read_command and not memory_write_command:
        raise ConfigError("workflow.memory_read_command requires workflow.memory_write_command")

    return ProjectConfig(
        project=ProjectInfo(name=name, language=language, framework=framework),
        commands=command_set,
        quality=gate,
        git=GitPolicy(
            base_branch=_nonempty_string(git["base_branch"], "git.base_branch"),
            isolated_branch=_bool(git["isolated_branch"], "git.isolated_branch"),
            allow_commit=_bool(git["allow_commit"], "git.allow_commit"),
        ),
        memory=MemoryPolicy(enabled=memory_enabled, workspace=workspace, project=memory_project),
        workflow=WorkflowPolicy(
            max_review_rounds=max_review_rounds,
            developer_command=developer_command,
            judge_command=judge_command,
            memory_write_command=memory_write_command,
            memory_read_command=memory_read_command,
        ),
    )


def _exact_keys(data: dict[str, object], expected: tuple[str, ...], label: str) -> None:
    found = set(data)
    required = set(expected)
    missing = sorted(required - found)
    extra = sorted(found - required)
    if missing or extra:
        raise ConfigError(f"{label} keys mismatch; missing={missing or '-'} extra={extra or '-'}")


def _object(value: object, label: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ConfigError(f"{label} must be an object")
    return value


def _bool(value: object, label: str) -> bool:
    if not isinstance(value, bool):
        raise ConfigError(f"{label} must be a boolean")
    return value


def _nonempty_string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f"{label} must be a non-empty string")
    return value.strip()


def _optional_string(value: object, label: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f"{label} must be a string or null")
    return value.strip()


def _optional_command(value: object, label: str) -> str | None:
    command = _optional_string(value, label)
    if command is None:
        return None
    if "\n" in command or "\r" in command:
        raise ConfigError(f"{label} must be a single line")
    if contains_secret(command):
        raise ConfigError(f"{label} contains credential-shaped text")
    return command


def _bounded_int(value: object, label: str, low: int, high: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ConfigError(f"{label} must be an integer")
    if value < low or value > high:
        raise ConfigError(f"{label} must be between {low} and {high}")
    return value
