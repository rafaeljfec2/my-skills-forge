# PLAN phase obligations

Read this reference only while the run is in **PLAN**. Canonical SDD phase law lives in `sdd-workflow`; this file binds Connexto artifacts to those obligations.

## SDD obligations in PLAN

- Produce **spec.md**, **plan.md**, and **tasks.md** under the run directory (see [templates/](../templates/) for headings).
- Scope change after PLAN → return to PLAN with reason `scope_change` or `inconsistent_plan` (engine transition).
- Researcher output must stay `Implemented: no` in **research.md**.

## Required headings

| File | Required section |
|---|---|
| `spec.md` | `## Behavior` |
| `plan.md` | `## Acceptance criteria` |
| `tasks.md` | At least one open task (`- [ ]`) |

Engine preconditions for `PLAN → IMPLEMENT` (`plan_accepted`) reject missing sections or tasks with no open item. The engine does not see the reviewer. The agent must still record an independent SPEC review before that transition.

## Independent SPEC review

Before `plan_accepted`, spawn a **separate readonly subagent** with a fresh context. Use a different actor id from the planner. Follow the Phase 3 spawn in `sdd-workflow` `references/pipeline-phases.md`.

- `APPROVED` → transition to IMPLEMENT in the same run. Do not ask the operator.
- `NEEDS_FIX` → revise `spec.md` and spawn a new review.
- `STOP` → inconsistency or unresolved doubt. Stop and ask the operator. Do not implement.

The planner does not approve its own spec. A self-`APPROVED` spec does not satisfy this gate.

## Templates

Start from [templates/spec.md](../templates/spec.md), [templates/plan.md](../templates/plan.md), and [templates/tasks.md](../templates/tasks.md). Keep identifiers and code in English; operator-facing summaries may follow conversation language.

## Authoring hygiene

During IMPLEMENT (not PLAN), apply `principal-engineering-workflow` including [refactoring.md](../../principal-engineering-workflow/references/refactoring.md) when reshaping code.
