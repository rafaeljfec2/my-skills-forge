"""Default workflow section for connexto.project.json."""

from __future__ import annotations


def default_workflow() -> dict[str, object]:
    return {
        "max_review_rounds": 3,
        "developer_command": None,
        "judge_command": None,
        "memory_write_command": None,
        "memory_read_command": None,
    }
