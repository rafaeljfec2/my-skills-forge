# Protocol workflow steps 1–7

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
