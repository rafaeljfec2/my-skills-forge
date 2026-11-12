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

Engine preconditions for `PLAN → IMPLEMENT` (`plan_accepted`) reject missing sections or tasks with no open item.

## Templates

Start from [templates/spec.md](../templates/spec.md), [templates/plan.md](../templates/plan.md), and [templates/tasks.md](../templates/tasks.md). Keep identifiers and code in English; operator-facing summaries may follow conversation language.

## Authoring hygiene

During IMPLEMENT (not PLAN), apply `principal-engineering-workflow` including [refactoring.md](../../principal-engineering-workflow/references/refactoring.md) when reshaping code.
