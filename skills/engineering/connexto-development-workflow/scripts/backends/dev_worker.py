#!/usr/bin/env python3
"""Reference developer backend: reads task.json and writes calc.py plus report.json."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def main() -> int:
    task_path = Path(os.environ["CDW_DEVELOPER_TASK"])
    report_path = Path(os.environ["CDW_DEVELOPER_REPORT"])
    repo = Path(os.environ["CDW_REPO"])
    session = os.environ.get("CDW_DEVELOPER_SESSION", "dev-session")
    task = json.loads(task_path.read_text(encoding="utf-8"))
    scope = str(task.get("artifacts", {}).get("plan", "") or "")
    if "calc" in str(task.get("objective", "")).lower() or "sum_values" in json.dumps(task):
        calc = repo / "calc.py"
        calc.write_text("def sum_values(values):\n    return sum(values)\n", encoding="utf-8")
        files = ["calc.py"]
    else:
        files = []
    try:
        rel = str(report_path.relative_to(repo))
    except ValueError:
        rel = str(report_path)
    report = {
        "report_version": 1,
        "summary": "Implemented the planned change in the target repository.",
        "files_changed": files,
        "tests_touched": ["test_calc.py"]
        if (repo / "test_calc.py").is_file()
        else (["test_ok.py"] if (repo / "test_ok.py").is_file() else []),
        "commands_run": [],
        "results": ["Wrote implementation files from the structured task."],
        "issues": [],
        "pending": [],
        "evidence_refs": [rel],
        "developer_session_id": session,
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
