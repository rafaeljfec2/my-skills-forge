---
name: error-plan-then-fix
description: >-
  When the user shares error output (stack traces, ESLint/TS failures, Husky or
  lint-staged logs, CI logs, git-error excerpts, test failures, build errors),
  runs a short planning phase then implements fixes. Use when the user pastes
  errors, attaches failure logs, or asks to fix, debug, or resolve an error.
---

# Error: plan first, then fix

## When this skill applies

Read and follow this skill when the user message **includes or references** any of:

- Pasted terminal or editor output with `error`, `FAILED`, `✖`, stack traces
- Paths like `git-error-*`, `husky`, `lint-staged`, pre-commit failures
- CI/job logs, `eslint`, `tsc`, `vitest`, `jest`, build failures
- Explicit asks: "fix this error", "fix this", "why did this fail"

If the user is in **Ask / read-only** mode, run **only** the planning phase and do not edit files or run mutating commands.

## Phase 1 — Planning mode (required)

Before changing code or running fixes:

1. **Extract signals**: tool (ESLint, Git, Turbo, and so on), cited files and lines, exit code.
2. **Hypotheses**: list 2–4 plausible causes, ordered by probability.
3. **Phased plan**: concrete steps (for example: confirm the file on disk versus the index, adjust config, fix the rule, validate with lint or a test).

If critical context is missing (wrong repo, unknown command, truncated error), ask **1–3** direct questions and only then close the plan.

If the UI is in **Plan mode**, use Cursor's plan tool. Otherwise, present the plan in clear markdown (title, causes, phases, files touched).

**Do not** jump to implementation without this block, unless the error is trivial and the plan is one explicit line (for example: "obvious typo on line X").

## Phase 2 — Resolve

After the plan (and after plan approval, when the product requires explicit confirmation):

1. Investigate with tools (read files, grep, verification commands).
2. Apply the **smallest fix** that is required, and follow the repo conventions.
3. Validate with the lint, test, or build that matches the error. Do not assume success without running the check that applies.
4. Summarize what failed, what changed, and how to validate.

## Constraints

- Do not edit `.env` secrets without explicit user authorization.
- Do not run destructive commands or `git push` without confirmation when the user's rules require it.
- Write code and identifiers in English. Respond to the user in Brazilian Portuguese unless they ask otherwise.

## Anti-patterns

- Fixing blindly, without a plan, when the log is long or ambiguous.
- Changing product behavior or refactoring outside the error's scope without a reason.
- Ignoring that the **Git index** can differ from the working tree (lint-staged fails on the index).
