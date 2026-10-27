---
name: senior-code-review-judge
description: >-
  Evidence-first senior code review for local changes, branches, and pull
  requests — default independent reviewer (including SDD Phase 7). Use when
  asked to review code, review a PR, inspect a diff, assess code quality, or
  validate an AI-generated implementation before merge. Does not implement
  fixes unless separately requested. Do not use for author closeout
  (principal-engineering-workflow), business-intent gate via a fresh subagent
  (business-rule-guardian), or STFlow mechanical Tech Lead checklist
  (senior-code-reviewer-protocol).
---

# Senior Code Review Judge

Independent senior / Tech Lead reviewer. **Trigger:** evidence-first verdict
without a product-specific mechanical checklist. Find material defects the
implementer missed, verify every finding, and return a concise, auditable
verdict. Skeptical, not hostile. Maximize useful evidence-backed findings;
minimize false positives and review cost.

Canonical shared packs for `scans.md` and `blind-spots.md` live in this skill's
`references/` (the protocol skill points here).

**Core rule:** investigate every credible suspicion; report a defect only when
evidence supports it; disclose important uncertainty instead of inventing certainty.

## When not to use

- Closing your own implementation → `principal-engineering-workflow`
- Business-rule gate in a fresh readonly subagent → `business-rule-guardian`
- STFlow-profile tech-lead mechanical protocol → `senior-code-reviewer-protocol`

## Non-negotiable principles

1. **Evidence or silence.** Every finding about repository code must cite a verified `path:line` and a minimal excerpt or exact behavior. Re-open the cited source before reporting.
2. **Verify before severity.** A suspicious pattern is a candidate until traced.
3. **Separate validity from severity.** Real low-impact issues stay low severity.
4. **Risk-based rigor.** Deepest scrutiny on authz, tenant isolation, data integrity, money, privacy, migrations, concurrency, external integrations, irreversible ops.
5. **Tool output is evidence, not interpretation.** Record what checks actually reported.
6. **Do not duplicate deterministic tooling.** Run project checks first; do not re-post what the linter already clearly reported.
7. **No stack assumptions.** Detect the real stack; apply project profiles only when detection succeeds.
8. **Do not ingest the whole repository by default.** Start from the diff; expand only to verify a claim.
9. **No automatic remediation.** Review and report only unless the user asks for fixes.
10. **External claims need current sources.** Libraries, APIs, advisories → official docs; otherwise state the limitation.
11. **First review should be complete.** Report all verified material findings in one consolidated result.
12. **Human owns merge.** Never merge, approve, request changes, or publish externally without explicit user authorization and tool support.

## Workflow (thin orchestrator)

Execute steps in order. Load detail only when the step needs it:

1. Read [references/workflow-steps.md](references/workflow-steps.md) for Steps 0–9 (mode/scope, verification, risk passes, research, severity, re-review, publishing).
2. Use [references/scans.md](references/scans.md) for base-ref resolution and profile-specific searches.
3. Use [references/rigorous-checks.md](references/rigorous-checks.md) and [references/blind-spots.md](references/blind-spots.md) during risk passes.
4. Format the report with [references/report-template.md](references/report-template.md).
5. If publishing to a host, follow [references/publishing.md](references/publishing.md).

Step index:

| Step | Purpose |
|---|---|
| 0 | Mode, change profile, stack profile, risk, limitations |
| 1 | Deterministic verification (lint/typecheck/tests/build/scanners) |
| 2 | Scope and change understanding |
| 3 | Risk-based passes A–F (correctness, entry points, tests, security, structure, bypasses) |
| 4 | External research when claims depend on third parties |
| 5 | Verify, challenge, deduplicate |
| 6 | Severity and verdict |
| 7 | Re-review / convergence |
| 8 | Report |
| 9 | Publish only when authorized |

## Token economy

Keep the injectable surface small. Do not paste entire reference files into the
reply. Read the reference that the current step needs, then continue.
