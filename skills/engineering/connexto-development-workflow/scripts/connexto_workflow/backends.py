"""Optional subprocess backends for developer, judge, and memory transports."""

from __future__ import annotations

import json
import os
import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path

from connexto_workflow.commands import split_command
from connexto_workflow.errors import WorkflowError
from connexto_workflow.redact import redact


@dataclass(frozen=True)
class BackendResult:
    exit_code: int | None
    timed_out: bool
    stdout: str
    stderr: str

    @property
    def passed(self) -> bool:
        return self.exit_code == 0 and not self.timed_out


def run_backend(command: str, env: dict[str, str], cwd: Path, timeout: int) -> BackendResult:
    argv = split_command(command)
    merged = os.environ.copy()
    merged.update(env)
    timed_out = False
    try:
        completed = subprocess.run(
            argv,
            cwd=str(cwd),
            env=merged,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        return BackendResult(
            exit_code=completed.returncode,
            timed_out=False,
            stdout=redact(completed.stdout),
            stderr=redact(completed.stderr),
        )
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        stdout = _decode(exc.stdout)
        stderr = _decode(exc.stderr)
        return BackendResult(exit_code=None, timed_out=timed_out, stdout=redact(stdout), stderr=redact(stderr))
    except OSError as exc:
        raise WorkflowError(f"backend failed to start: {exc.strerror or exc}") from exc


def parse_json_stdout(result: BackendResult, label: str) -> dict[str, object]:
    if not result.passed:
        detail = result.stderr.strip() or result.stdout.strip() or label
        raise WorkflowError(detail)
    text = result.stdout.strip()
    if not text:
        raise WorkflowError(f"{label} produced no stdout JSON")
    data = json.loads(text)
    if not isinstance(data, dict):
        raise WorkflowError(f"{label} stdout is not a JSON object")
    return data


def _decode(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if isinstance(value, str):
        return value
    return ""
