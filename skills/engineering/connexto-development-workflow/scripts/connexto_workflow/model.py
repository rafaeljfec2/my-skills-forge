"""States, edges, and risk ranks. The lifecycle reference must list every edge."""

from __future__ import annotations

DEMAND_TYPES: dict[str, str] = {
    "FEATURE": "FEAT",
    "BUGFIX": "BUG",
    "REFACTOR": "REFACTOR",
    "HOTFIX": "HOTFIX",
    "TECHNICAL_DEBT": "DEBT",
}

DEFAULT_RISK: dict[str, str] = {
    "FEATURE": "MEDIUM",
    "BUGFIX": "LOW",
    "REFACTOR": "MEDIUM",
    "HOTFIX": "HIGH",
    "TECHNICAL_DEBT": "LOW",
}

RISK_RANK: dict[str, int] = {"LOW": 1, "MEDIUM": 2, "HIGH": 3}

BLOCKING_SEVERITIES: dict[str, frozenset[str]] = {
    "LOW": frozenset({"critical", "blocking"}),
    "MEDIUM": frozenset({"critical", "blocking", "important"}),
    "HIGH": frozenset({"critical", "blocking", "important"}),
}

PROTECTED_ACTIONS: frozenset[str] = frozenset(
    {
        "merge_protected",
        "production_publish",
        "destructive_database",
        "infrastructure_change",
        "secret_rotation",
        "irreversible",
        "permission_change",
    }
)

TERMINAL: frozenset[str] = frozenset({"DONE", "FAILED", "CANCELLED"})

ACTIVE: frozenset[str] = frozenset(
    {
        "INTAKE",
        "RESEARCH",
        "PLAN",
        "IMPLEMENT",
        "VALIDATE",
        "REVIEW",
        "DELIVERY",
        "MEMORY",
    }
)

# reason set per edge. INTERNAL_ONLY edges run through engine operations, not `transition`.
EDGES: dict[tuple[str, str], frozenset[str]] = {
    ("PENDING", "INTAKE"): frozenset({"start"}),
    ("INTAKE", "RESEARCH"): frozenset({"intake_complete"}),
    ("RESEARCH", "PLAN"): frozenset({"research_complete"}),
    ("RESEARCH", "RESEARCH"): frozenset({"insufficient_research"}),
    ("PLAN", "IMPLEMENT"): frozenset({"plan_accepted"}),
    ("PLAN", "PLAN"): frozenset({"inconsistent_plan", "scope_change"}),
    ("IMPLEMENT", "PLAN"): frozenset({"scope_change"}),
    ("IMPLEMENT", "VALIDATE"): frozenset({"implementation_ready"}),
    ("VALIDATE", "REVIEW"): frozenset({"validation_passed"}),
    ("VALIDATE", "IMPLEMENT"): frozenset({"validation_failed"}),
    ("VALIDATE", "FAILED"): frozenset({"attempts_exhausted"}),
    ("REVIEW", "DELIVERY"): frozenset({"review_clear"}),
    ("REVIEW", "IMPLEMENT"): frozenset({"review_defect"}),
    ("REVIEW", "PLAN"): frozenset({"review_solution_failure"}),
    ("DELIVERY", "MEMORY"): frozenset({"delivery_recorded"}),
    ("MEMORY", "DONE"): frozenset({"memory_recorded", "memory_skipped"}),
}

INTERNAL_ONLY: frozenset[tuple[str, str]] = frozenset(
    {
        ("IMPLEMENT", "VALIDATE"),
        ("VALIDATE", "REVIEW"),
        ("VALIDATE", "IMPLEMENT"),
        ("VALIDATE", "FAILED"),
        ("REVIEW", "DELIVERY"),
        ("REVIEW", "IMPLEMENT"),
        ("REVIEW", "PLAN"),
        ("MEMORY", "DONE"),
    }
)

EDGE_ROLES: dict[tuple[str, str], frozenset[str]] = {
    ("PENDING", "INTAKE"): frozenset({"orchestrator"}),
    ("INTAKE", "RESEARCH"): frozenset({"orchestrator"}),
    ("RESEARCH", "PLAN"): frozenset({"researcher", "orchestrator"}),
    ("RESEARCH", "RESEARCH"): frozenset({"researcher", "orchestrator"}),
    ("PLAN", "IMPLEMENT"): frozenset({"planner", "orchestrator"}),
    ("PLAN", "PLAN"): frozenset({"planner", "orchestrator"}),
    ("IMPLEMENT", "PLAN"): frozenset({"developer", "planner", "orchestrator"}),
    ("IMPLEMENT", "VALIDATE"): frozenset({"developer", "orchestrator"}),
    ("VALIDATE", "REVIEW"): frozenset({"developer", "orchestrator"}),
    ("VALIDATE", "IMPLEMENT"): frozenset({"developer", "orchestrator"}),
    ("VALIDATE", "FAILED"): frozenset({"developer", "orchestrator"}),
    ("REVIEW", "DELIVERY"): frozenset({"reviewer"}),
    ("REVIEW", "IMPLEMENT"): frozenset({"reviewer"}),
    ("REVIEW", "PLAN"): frozenset({"reviewer"}),
    ("DELIVERY", "MEMORY"): frozenset({"orchestrator"}),
    ("MEMORY", "DONE"): frozenset({"orchestrator"}),
}

NEXT_STEP: dict[str, str] = {
    "PENDING": "transition to INTAKE with reason start",
    "INTAKE": "transition to RESEARCH with reason intake_complete",
    "RESEARCH": "write research.md, then transition to PLAN with reason research_complete",
    "PLAN": "write spec.md, plan.md, and tasks.md, then transition to IMPLEMENT",
    "IMPLEMENT": "materialize developer/task.json, run the developer agent or run-developer, submit develop-report, then validate",
    "VALIDATE": "validation is in progress; reload and continue validate",
    "REVIEW": "run-judge with a reviewer session id, or submit review.json when judge_command is null",
    "DELIVERY": "compose the delivery report, then transition to MEMORY",
    "MEMORY": "memory-sync when remote commands are configured, else memory-payload and memory-ack",
    "WAITING_APPROVAL": "approve the pending action with a different actor id",
    "BLOCKED": "unblock after the recorded dependency is available",
    "DONE": "run is complete",
    "FAILED": "run failed; start a new demand id to try again",
    "CANCELLED": "run was cancelled",
}

PUTTABLE: frozenset[str] = frozenset({"research.md", "spec.md", "plan.md", "tasks.md"})

PUT_ROLES: dict[str, frozenset[str]] = {
    "research.md": frozenset({"researcher", "orchestrator"}),
    "spec.md": frozenset({"planner", "orchestrator"}),
    "plan.md": frozenset({"planner", "orchestrator"}),
    "tasks.md": frozenset({"planner", "orchestrator"}),
}
