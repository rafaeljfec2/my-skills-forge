---
name: principal-engineering-workflow
description: >-
  Default engineering workflow for delivery-quality work. After every
  implementation (feature, bug fix, refactor), requires a meticulous self code
  review, concrete correction proposals, applying fixes, and validating with
  lint/tests/build before closing the task. Use whenever implementing code or
  shipping changes. Do not use for independent PR verdict without authoring
  (senior-code-review-judge), mandatory fresh-subagent business gate
  (business-rule-guardian), or STFlow tech-lead checklist
  (senior-code-reviewer-protocol).
---

# Principal engineering workflow

Mandatory closure after any implementation. Default bar for finished work.

## When not to use

- Independent evidence-first PR review (no authoring) → `senior-code-review-judge`
- Business-rule gate in a fresh readonly subagent → `business-rule-guardian`
- STFlow mechanical tech-lead checklist → `senior-code-reviewer-protocol`

## When to apply

- Whenever you have **changed code** in response to a request
- Before declaring the task **done** or asking for merge/PR

## Workflow (thin orchestrator)

1. **Careful self-review** — architecture/boundaries, correctness/edges, security, perf/observability, project standards, tests (English descriptions), lint/types/format.
2. **Propose corrections** — critical / important / minor; what, where, why.
3. **Adjust the code** — apply safe fixes; confirm large/ambiguous ones with the user.
4. **Validate** — lint, build, tests in touched packages; IDE Problems on changed files.
5. **Reply** — short technical summary + remaining risks; Brazilian Portuguese unless the user asked otherwise.

For deeper review, also follow `senior-code-review-judge` and/or `senior-code-reviewer-protocol`. For auth/sensitive data, follow `application-security-expert`.

## What to avoid

- Closing with only "done" and no review/validation
- Changing `.env` or secrets without explicit user authorization

## Token economy

Keep the injectable surface small. This skill is the closure checklist; load sibling review skills only when their depth is required.
