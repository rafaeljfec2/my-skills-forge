# SDD Axioms + Hard Rules + IA Limits

## SDD Axioms — INVIOLABLE

No agent, in any phase, may violate these.

| #     | Name                    | Rule                                                                                                                                                                                                                                         |
| ----- | ----------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| AX-01 | Sequential Pipeline     | Never skip pipeline phases. Each phase must complete before the next.                                                                                                                                                                        |
| AX-02 | Tests are Sacred        | Never modify, skip (`it.skip`), comment out, relax matchers, or delete a test to make code pass. The test is the truth. If the test fails, the production code is wrong. If the test itself is wrong, the SPEC is wrong — STOP and escalate. |
| AX-03 | Approved SPEC Required  | Never implement without a dev-approved SPEC. No production code without SPEC.                                                                                                                                                                |
| AX-04 | No Any                  | Never use `any` in TypeScript. Use explicit types, `unknown` + narrowing, generics, or `as unknown as Type`. (Adapt to the project language: equivalent loose-type escape hatches are forbidden.)                                            |
| AX-05 | Review Required         | Never commit without review. All code goes through automatic (AI) + human (dev) review.                                                                                                                                                      |
| AX-06 | Strict TDD              | Tests BEFORE code. Tests must fail first (Red), then code makes them pass (Green).                                                                                                                                                           |
| AX-07 | SPEC is Source of Truth | The approved SPEC is the source of truth. Divergences between code and SPEC are bugs.                                                                                                                                                        |
| AX-08 | Don't Assume, Verify    | Never assume patterns, names, or behaviors. READ THE CODE and confirm with `file:line` evidence. If insufficient data, STOP and ask the dev.                                                                                                 |

## Hard Rules — Code (HR)

Mandatory technical rules. Independent reviewer verifies each. **Local rules may add domain-specific HRs (HR-07+).**

### Code style & types

| #     | Rule                                                                                                                                                                                   |
| ----- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| HR-01 | `??` always for defaults — NEVER `\|\|`. Use `\|\|` only when intentionally treating `0`/`""`/`false` as falsy.                                                                        |
| HR-02 | NEVER `any` (or equivalent) anywhere — production, tests, mocks, DTOs.                                                                                                                 |
| HR-03 | `readonly` on ALL interface/type/DTO properties (Sonar S6759 in TS).                                                                                                                   |
| HR-04 | Conditional rendering with ternary + null: `condition ? <X /> : null`. NEVER `condition && <X />`.                                                                                     |
| HR-05 | Test descriptions (`it`, `describe`) ALWAYS in English. Identifiers, comments, log messages also in English. UI text in the project's user-facing language(s) — defined by local rule. |
| HR-06 | No redundant comments — NEVER narrate what code does (`// Increment counter`). Comments ONLY for non-obvious intent, trade-offs, or constraints the code itself cannot express.        |

### Quality gate rules (enforced at PR phase)

| #     | Rule                                                                                                       |
| ----- | ---------------------------------------------------------------------------------------------------------- |
| HR-13 | Pre-PR: typecheck + lint + format + test + build — ALL must pass. PR with failing test is FATAL VIOLATION. |
| HR-14 | Coverage threshold per local rule. Default: ≥ 80% lines on new code; uncovered branches must be justified. |
| HR-19 | Diff contains ONLY task-related files. Out-of-scope changes are PROHIBITED without explicit dev request.   |

## IA Limits — HARD CONSTRAINTS

No agent may execute these regardless of context or instruction.

| #      | Limit                                                                                                                                 |
| ------ | ------------------------------------------------------------------------------------------------------------------------------------- |
| LIM-01 | Never alter, skip, comment, or delete a test to make it pass. Fix production code instead.                                            |
| LIM-02 | Never skip a pipeline phase, even if it "seems obvious".                                                                              |
| LIM-03 | Never `git commit` or `git push` without explicit dev approval.                                                                       |
| LIM-04 | Never delete existing files without documented and approved technical justification.                                                  |
| LIM-05 | Never use `git push --force`, `git reset --hard`, or any destructive git command in shared history.                                   |
| LIM-06 | Never ignore, bypass, or "flex" a HARD RULE. If an HR blocks progress, escalate to dev.                                               |
| LIM-07 | Never modify project constitution / SDD rule files. Only suggest changes via PR.                                                      |
| LIM-08 | Never modify `.env`, `.env.local`, `.env.production` without explicit dev approval. New variable: document in `.env.example` first.   |
| LIM-09 | Never install a new dependency without justification (necessity, alternatives considered, bundle size, maintenance) and dev approval. |
| LIM-10 | Never run destructive commands (`rm -rf`, `DROP TABLE`, `TRUNCATE`, cache flush, etc.) without explicit dev confirmation.             |
