"""Run configured commands and append redacted results. The shell is not used."""

from __future__ import annotations

import json
import shlex
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from connexto_workflow.errors import ConfigError, WorkflowError
from connexto_workflow.redact import redact

_EXCERPT_LIMIT = 4000


@dataclass(frozen=True)
class CommandRecord:
    name: str
    argv: list[str]
    exit_code: int | None
    timed_out: bool
    stdout_excerpt: str
    stderr_excerpt: str
    started_at: str
    finished_at: str

    @property
    def passed(self) -> bool:
        return self.exit_code == 0 and not self.timed_out


def split_command(command: str) -> list[str]:
    argv = shlex.split(command, posix=True)
    if not argv:
        raise ConfigError("command resolved to an empty argv")
    return argv


def run_command(repo: Path, name: str, command: str, timeout: int, log_path: Path) -> CommandRecord:
    argv = split_command(command)
    started = _now()
    timed_out = False
    exit_code: int | None
    try:
        completed = subprocess.run(
            argv,
            cwd=repo,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        stdout = completed.stdout
        stderr = completed.stderr
        exit_code = completed.returncode
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        exit_code = None
        stdout = _bytes_or_str(exc.stdout)
        stderr = _bytes_or_str(exc.stderr)
    except OSError as exc:
        raise WorkflowError(f"failed to execute {name}: {exc.strerror or exc}") from exc
    finished = _now()
    record = CommandRecord(
        name=name,
        argv=[redact(part) for part in argv],
        exit_code=exit_code,
        timed_out=timed_out,
        stdout_excerpt=redact(stdout)[:_EXCERPT_LIMIT],
        stderr_excerpt=redact(stderr)[:_EXCERPT_LIMIT],
        started_at=started,
        finished_at=finished,
    )
    _append_jsonl(log_path, asdict(record))
    return record


def _append_jsonl(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _bytes_or_str(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if isinstance(value, str):
        return value
    return ""
