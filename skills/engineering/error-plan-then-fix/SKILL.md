---
name: error-plan-then-fix
description: >-
  When the user shares error output (stack traces, ESLint/TS failures, Husky or
  lint-staged logs, CI logs, git-error excerpts, test failures, build errors),
  runs a short planning phase then implements fixes. Use when the user pastes
  errors or asks to fix/debug/resolve an error.
---

# Error: plan first, then fix

## When this skill applies

- Pasted terminal/editor output with `error`, `FAILED`, stack traces
- `git-error-*`, husky, lint-staged, pre-commit failures
- CI logs, eslint, tsc, vitest, jest, build failures
- Explicit asks: "fix this error", "why did this fail"

If the user is in Ask / read-only mode, run **only** the planning phase.

## Workflow (thin orchestrator)

### Phase 1 — Planning (required)

1. Extract signals: tool, files/lines, exit code
2. Hypotheses: 2–4 causes by probability
3. Phased plan: concrete steps

Ask 1–3 questions if critical context is missing. Do not jump to implementation unless the error is trivial (one-line plan).

### Phase 2 — Resolve

1. Investigate with tools
2. Smallest fix that matches repo conventions
3. Validate with the matching lint/test/build
4. Summarize failure, change, validation

## Constraints

- No `.env` secret edits without authorization
- No destructive git/push without required confirmation
- Code/identifiers in English; user replies in Brazilian Portuguese unless asked otherwise

## Anti-patterns

- Blind fixes on long/ambiguous logs
- Out-of-scope refactors
- Ignoring Git index vs working tree (lint-staged)

## Token economy

Keep the injectable surface small. Plan first; load only the files needed to verify the fix.
