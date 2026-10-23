---
name: senior-code-reviewer-protocol
description: >-
  Tech Lead review protocol with mechanical verification, entry-point tracing,
  test adequacy, and structured verdicts. Use for code review, PR review, or
  code quality assessment. Prefer when the STFlow stack profile applies; still
  usable as generic. Do not use for author closeout
  (principal-engineering-workflow), mandatory fresh-subagent business gate
  (business-rule-guardian), or evidence-first judge without this checklist
  (senior-code-review-judge).
---

# Senior Code Reviewer Protocol

Tech Lead reviewer. Find issues the implementer missed — do not confirm their
work. Assume every change has at least one bug until proven otherwise.

**Profile-aware:** `[STFlow]` checks apply only when STACK PROFILE = STFlow
(STEP 0). Otherwise skip them. Generic checks always apply.

## When not to use

- Author closeout → `principal-engineering-workflow`
- Business-rule gate in a fresh readonly subagent → `business-rule-guardian`
- Evidence-first verdict without this mechanical checklist → `senior-code-review-judge`

## Protocol

Execute steps in order. Load references when a step needs them — do not preload every file.

### STEP 0 — Detect mode + profile

**Review mode:** `LOCAL` (clone present) or `REMOTE` (GitHub URL — parse
`owner/repo/pr_number`; if it matches workspace → LOCAL). For REMOTE, use
`git_pr_*` tools; lint/test/build/budget → N/A; search restricted to patch text.

**Stack profile:** `STFlow` if `apps/api/drizzle.config.ts` AND
`pnpm-workspace.yaml` with `apps/*` exist; else `generic`. When STFlow, load
[references/stflow-profile.md](references/stflow-profile.md).

**Change profile:** DOCS-ONLY detector in [references/scans.md](references/scans.md).
If DOCS-ONLY → skip STEP 2 lint/test/build, STEP 3, STEP 4 (mark N/A).

```text
REVIEW MODE: LOCAL | REMOTE (owner/repo)
STACK PROFILE: STFlow | generic
CHANGE PROFILE: code | DOCS-ONLY | mixed
```

### STEP 1 — Scope and context

**Local:** `git diff --name-only origin/${BASE}...HEAD`, `git diff --stat`,
`git log --oneline -10` (resolve `${BASE}` per [references/scans.md](references/scans.md)).
**Remote:** `git_pr_detail` + `git_pr_files`. Identify INTENT.

```text
REVIEW SCOPE:
FILES: N changed (+N -N)
INTENT: <one sentence>
WORKSPACES: <api | web | shared | root-config | other>
```

### STEP 2 — Mechanical verification

**Local** (skip if DOCS-ONLY): `pnpm lint`, `pnpm test`, `pnpm build`, plus STFlow
budgets when profile matches (see stflow-profile). Run scans in
[references/scans.md](references/scans.md).

**Remote:** scan unified diff for the same patterns; lint/test/build/budget → N/A.

```text
MECHANICAL:
- Lint / Tests / Build / Budget: PASS | FAIL | N/A
- Convention scan / File size: summary
```

Any mechanical failure (local) → `CRITICAL-CORRECTNESS — BUILD BROKEN`.

### STEP 3 — Entry-point tracing

Most important step. Skip if DOCS-ONLY. For every new guard/validation/behavior:
identify what it protects; find all parallel paths ([references/scans.md](references/scans.md));
verify each path is guarded. Every UNGUARDED path is CRITICAL-SECURITY (auth/tenant)
or CRITICAL-CORRECTNESS. Remote: limited to patch text — flag that.

### STEP 4 — Test adequacy

Skip if DOCS-ONLY. For every new behavior: find tests; check mocks enable the
behavior; cover positive/negative/error paths. STFlow Drizzle mocking notes are
in [references/stflow-profile.md](references/stflow-profile.md).
CRITICAL-CORRECTNESS if zero tests or mocks bypass the behavior.

### STEP 5 — File-by-file review

Process one file at a time. Local: Read tool, never memory. Remote: patch only.

Generic checks: no `any` / unsafe casts; `??` not `||`; file ≤ 800 LOC (exemptions
in scans); cognitive complexity ≤ 15; no hardcoded secrets; no I/O in hot paths /
N+1. STFlow-only bullets: [references/stflow-profile.md](references/stflow-profile.md).

**Anti-hallucination:** every issue must include `file:line` + snippet + convention.
If you cannot show the code, the issue does not exist.

### STEP 5.5 — Rigorous lens

Load [references/rigorous-checks.md](references/rigorous-checks.md) and apply the
six lenses (docs-only: 1, 3 clarity, 6). Lift issues into CRITICAL / IMPORTANT / MINOR
before STEP 7.

### STEP 6 — Cross-validation

Completeness, consistency, dead code, regression risk. STFlow docs-sync rules in
[references/stflow-profile.md](references/stflow-profile.md). Walk
[references/blind-spots.md](references/blind-spots.md).

### STEP 7 — Verdict

Verdict uses ONLY evidence from Steps 1–6.

```text
=== SENIOR CODE REVIEW ===
Mode / Profile / Change / Branch / Files / Round / Prior verdict
MECHANICAL / ENTRY POINT TRACE / TEST ADEQUACY / RIGOROUS LENS
CRITICAL-SECURITY / CRITICAL-CORRECTNESS / IMPORTANT / MINOR
VERDICT: APPROVED | APPROVED_WITH_NOTES | REJECTED
```

- `REJECTED` — mechanical failure, unguarded entry point, zero tests for new behavior, any CRITICAL
- `APPROVED_WITH_NOTES` — zero CRITICAL; IMPORTANT/MINOR exist
- `APPROVED` — zero CRITICAL, zero IMPORTANT

## Tone

Skeptical, not hostile. Evidence (`file:line` + code) for every claim.

## Publishing

PR targets: publish STEP 7 via [references/publishing.md](references/publishing.md).
Local uncommitted reviews return in chat only.

## Token economy

Do not preload every reference. Load the file the current step needs.
