---
name: iterative-sdd-workflow
description: >-
  Run a manually invoked, lightweight SDD loop for auditing and delivering
  approved corrections one at a time. Do not use for explanation-only requests
  or standalone reviews that do not include implementation.
disable-model-invocation: true
---

# Iterative SDD Workflow

Use this workflow only when the user explicitly invokes this skill. Local
project rules and safety boundaries remain authoritative. Keep each correction
small, evidence-based, and independently reviewable; do not design a larger
system unless the approved correction requires it.

## When not to use

- Explanation-only requests or independent code review without implementation
  → answer directly or use `senior-code-review-judge`.
- A request for the canonical seven-phase SDD protocol → `sdd-workflow`.

## Workflow (thin orchestrator)

1. Read the relevant project instructions and inspect only the code, consumers,
   tests, and configuration needed to audit the requested scope.
2. Report findings before editing. For each finding, state its evidence, the
   smallest proposed correction, an observable acceptance claim, and how that
   claim can be verified. Keep findings as separate approval units.
3. Wait for explicit user approval for each correction. Implement one approved
   correction at a time; do not bundle unapproved findings or unrelated cleanup.
4. For a defect, reproduce it and add a regression test that fails before
   changing production code. Then make the smallest fix. If reproduction or a
   meaningful regression test is not possible, explain the blocker and ask how
   to proceed.
5. Run the claim-scoped checks and relevant project quality checks. Inspect the
   complete diff for correctness, scope, and consistency with the approved
   correction. Never weaken or remove a test to make the change pass.
6. Present the changed files, diff summary, verification evidence, and remaining
   risks. Wait for the user's acceptance before treating the correction as
   complete or moving to another correction.
7. After acceptance, prepare a concise release handoff. Commit, push, merge, or
   deploy only when separately requested and authorized. Propose a regression
   test or project instruction for a durable lesson; change persistent project
   instructions only with approval.

Do not create a comprehensive plan before the audit. Keep the correction record
to the intent, constraints, acceptance claim, and evidence path needed for that
unit of work. If the audit finds no actionable issue, report that without
manufacturing changes.

## Token economy

Load only the project context and validation instructions needed for the current
correction. Report concise evidence and link to relevant files rather than
repeating source content.
