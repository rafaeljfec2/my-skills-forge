---
name: connexto-development-workflow
description: >-
  Execute a software demand as a recoverable state machine (intake, research,
  plan, implement, validate, independent review, delivery, AI Memory) using the
  target repo's connexto.project.json. After the demand is triggered, continue
  until DONE. Stop only for an inconsistency, an unresolved doubt, or a
  protected action. SPEC approval is a separate readonly agent. Use for
  FEATURE, BUGFIX, REFACTOR, HOTFIX, and TECHNICAL_DEBT work that must survive
  interruption. Do not use for one manually approved correction
  (iterative-sdd-workflow), SDD phase law alone (sdd-workflow), or author
  self-review (principal-engineering-workflow).
---

# Connexto development workflow

Executable delivery loop for a target repository. Roles share one runtime;
actor ids and writable artifacts stay separated. Methodology stays in the
existing skills. This skill owns state, gates, evidence, and the project adapter.

## Core contract (non-negotiable)

- Persist `state.json` under `.connexto/runs/<id>/` before stopping; chat is not recovery.
- After the operator triggers a demand, drive every state through DONE in the same run. Do not pause for the operator to confirm intake, spec, or design.
- **Stop and ask only** when an inconsistency or a doubt that would change the outcome cannot be resolved from the repo or a fresh reviewer, when the run is BLOCKED or FAILED, or when a protected action is waiting (merge, production, destructive, infrastructure, secrets, irreversible, permission).
- **SPEC approval** before `plan_accepted` is a separate readonly subagent with a fresh context and a different actor id. The planner does not approve its own spec. On `APPROVED`, transition immediately.
- `start_high_risk` is the same pattern: a different actor in a fresh context approves a coherent brief. Do not ask the operator unless that review reports an inconsistency or a doubt.
- Operators and agents drive transitions only through **`cdw.py`** (no ad-hoc state edits).
- When `commands.implement` is null, the developer must submit **`developer/report.json`** (or a successful implement hook).
- **REVIEW** uses a different actor/session than **IMPLEMENT**; same actor is rejected.
- Remote memory counts only after **read-back** confirms the written body (see `memory-sync`).
- Do not declare **merge**, **production publish**, or **deploy** unless a protected approval was recorded.

## When not to use

- Canonical SDD phase rules → `sdd-workflow` (still binding inside PLAN and REVIEW)
- Author hygiene after edits → `principal-engineering-workflow`
- One correction with human acceptance between units → `iterative-sdd-workflow`
- Verdict-only review → `senior-code-review-judge`

## Workflow (thin orchestrator)

**Operator:** read [references/operator-usage.md](references/operator-usage.md) when the human only passes a demand in chat.

1. Read [references/project-adapter.md](references/project-adapter.md) and load `connexto.project.json`. Do not invent commands or a stack.
2. Read [references/lifecycle.md](references/lifecycle.md) and, for a multi-sprint queue, [references/campaign.md](references/campaign.md). Drive [scripts/cdw.py](scripts/cdw.py). Persist `.connexto/runs/<id>/state.json` before stopping. Campaign state stays in `.connexto/campaigns/<id>/state.json`.
3. INTAKE and RESEARCH: [references/roles.md](references/roles.md). The researcher does not edit product code.
4. PLAN: [references/planning.md](references/planning.md) (`sdd-workflow` obligations, required headings, template pointers). Before `plan_accepted`, spawn the independent SPEC review. Continue on `APPROVED`.
5. IMPLEMENT: materialize `developer/task.json`, implement in the repo, submit `developer/report.json` when `commands.implement` is null (optional `run-developer` backend). Prefer TDD when the project has a test command. Scope change → PLAN. Author hygiene: `principal-engineering-workflow`.
6. VALIDATE: run only configured commands. Record argv, working directory, exit code, and redacted output. The validator actor must differ from the developer. Failures return to IMPLEMENT until `quality.max_validate_attempts`.
7. REVIEW: spawn a **readonly** subagent (Task) running **`senior-code-review-judge`** with a different actor/session from IMPLEMENT; then submit `review.json` via `run-judge` when configured or `cdw.py review`. Actor id alone is not independent review. See [references/policies.md](references/policies.md).
8. DELIVERY and MEMORY: [references/artifacts.md](references/artifacts.md) and [references/memory.md](references/memory.md). Use `memory-sync` when remote commands are set. Do not claim merge, publish, or deploy.

## Token economy

Read only the reference for the current state. Do not paste the CLI source or sibling skills into the reply.
