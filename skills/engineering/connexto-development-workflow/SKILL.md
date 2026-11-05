---
name: connexto-development-workflow
description: >-
  Execute a software demand as a recoverable state machine (intake, research,
  plan, implement, validate, independent review, delivery, AI Memory) using the
  target repo's connexto.project.json. Use for FEATURE, BUGFIX, REFACTOR,
  HOTFIX, and TECHNICAL_DEBT work that must survive interruption. Do not use
  for one manually approved correction (iterative-sdd-workflow), SDD phase law
  alone (sdd-workflow), or author self-review (principal-engineering-workflow).
---

# Connexto development workflow

Executable delivery loop for a target repository. Roles share one runtime;
actor ids and writable artifacts stay separated. Methodology stays in the
existing skills. This skill owns state, gates, evidence, and the project adapter.

## When not to use

- Canonical SDD phase rules → `sdd-workflow` (still binding inside PLAN and REVIEW)
- Author hygiene after edits → `principal-engineering-workflow`
- One correction with human acceptance between units → `iterative-sdd-workflow`
- Verdict-only review → `senior-code-review-judge`

## Workflow (thin orchestrator)

**Operator:** read [references/operator-usage.md](references/operator-usage.md) when the human only passes a demand in chat.

1. Read [references/project-adapter.md](references/project-adapter.md) and load `connexto.project.json`. Do not invent commands or a stack.
2. Read [references/lifecycle.md](references/lifecycle.md). Drive [scripts/cdw.py](scripts/cdw.py). Persist `.connexto/runs/<id>/state.json` before stopping.
3. INTAKE and RESEARCH: [references/roles.md](references/roles.md). The researcher does not edit product code.
4. PLAN: follow the `sdd-workflow` phase obligations that apply. Write spec, plan, and tasks from [templates/](templates/).
5. IMPLEMENT: materialize `developer/task.json`, implement in the repo, submit `developer/report.json` when `commands.implement` is null (optional `run-developer` backend). Prefer TDD when the project has a test command. Scope change → PLAN. Author hygiene: `principal-engineering-workflow`.
6. VALIDATE: run only configured commands. Record argv, exit code, and redacted output. Failures return to IMPLEMENT until `quality.max_validate_attempts`.
7. REVIEW: different actor and session from the developer. Prefer `run-judge` when configured; otherwise readonly `senior-code-review-judge` and structured review JSON. See [references/policies.md](references/policies.md).
8. DELIVERY and MEMORY: [references/artifacts.md](references/artifacts.md) and [references/memory.md](references/memory.md). Use `memory-sync` when remote commands are set. Do not claim merge, publish, or deploy.

## Token economy

Read only the reference for the current state. Do not paste the CLI source or sibling skills into the reply.
