# PLAN phase obligations

Read this reference only while the run is in **PLAN**. Canonical SDD phase law lives in `sdd-workflow`; this file binds Connexto demand artifacts to those obligations.

A demand-level SDD plan and a campaign sprint execution plan are different artifacts. Do not use one as a substitute for the other.

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

## Template authority

- [`templates/plan.md`](../templates/plan.md) is the generic **demand-level SDD artifact** required by the Connexto run state machine. It is not the parser-visible campaign queue, not a campaign sprint execution plan, and not a substitute for a target project's sprint-plan template.
- When the demand is a campaign sprint or campaign-gate plan, read the target repository's `AGENTS.md` and always-applied project rules. Use the exact canonical sprint-plan template designated by that target repository.
- The canonical target-repository template and policy take precedence over generic templates shipped with this skill. Do not emit the legacy `references/sprint-execution-plan.md` format.
- If the target repository does not identify a canonical sprint-plan template, stop the dependent planning output as `BLOCKED` and identify the missing authority. Do not invent a template or silently fall back to `templates/plan.md`.
- The language of every artifact written inside the target repository follows that repository's artifact-language policy. The forge's PT-BR default is only a fallback when the target repository has no specific policy.

Start demand-level artifacts from [`templates/spec.md`](../templates/spec.md), [`templates/plan.md`](../templates/plan.md), and [`templates/tasks.md`](../templates/tasks.md). Keep identifiers and code in English. Campaign sprint plans still require exactly T1–T4, as in [campaign.md](campaign.md).

## Authoring hygiene

During IMPLEMENT (not PLAN), apply `principal-engineering-workflow` including [`refactoring.md`](../../principal-engineering-workflow/references/refactoring.md) when reshaping code.
