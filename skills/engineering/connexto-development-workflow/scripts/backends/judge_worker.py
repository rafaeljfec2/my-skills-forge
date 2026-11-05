#!/usr/bin/env python3
"""Reference judge backend for senior-code-review-judge structured output."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

SKILL = "senior-code-review-judge"


def main() -> int:
    bundle_path = Path(os.environ["CDW_JUDGE_INPUT"])
    output_path = Path(os.environ["CDW_JUDGE_OUTPUT"])
    session = os.environ["CDW_REVIEWER_SESSION"]
    round_number = int(os.environ.get("CDW_REVIEW_ROUND", "1"))
    repo = Path(os.environ["CDW_REPO"])
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    diff = str(bundle.get("diff", ""))
    records = bundle.get("command_records")
    passed = False
    if isinstance(records, list):
        test_records = [item for item in records if isinstance(item, dict) and item.get("name") == "test"]
        if test_records:
            latest = test_records[-1]
            passed = latest.get("exit_code") == 0 and latest.get("timed_out") is False
    calc = repo / "calc.py"
    body = calc.read_text(encoding="utf-8") if calc.is_file() else ""
    ok = (repo / "test_ok.py").is_file() and passed and not calc.is_file()
    if ok or ("def sum_values" in body and passed):
        payload = {
            "skill": SKILL,
            "verdict": "APPROVED",
            "summary": "calc.py defines sum_values and validation recorded a passing test.",
            "findings": [],
            "reviewer_session_id": session,
            "round": round_number,
        }
    else:
        payload = {
            "skill": SKILL,
            "verdict": "REJECTED",
            "summary": "Implementation does not satisfy acceptance from diff and validation.",
            "findings": [
                {
                    "severity": "critical",
                    "file": "calc.py",
                    "location": "sum_values",
                    "rationale": "Missing or failing sum_values relative to validation evidence.",
                    "return_to": "IMPLEMENT",
                }
            ],
            "reviewer_session_id": session,
            "round": round_number,
        }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    _ = diff
    return 0


if __name__ == "__main__":
    sys.exit(main())
