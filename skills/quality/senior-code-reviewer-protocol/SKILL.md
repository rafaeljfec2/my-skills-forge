---
name: senior-code-reviewer-protocol
description: >-
  STFlow-preferring Tech Lead review protocol with mechanical verification,
  entry-point tracing, test adequacy, and structured verdicts. Use when the
  STFlow stack profile applies or the user wants this checklist. Do not use for
  author closeout (principal-engineering-workflow), mandatory fresh-subagent
  business gate (business-rule-guardian), or evidence-first review without this
  checklist (senior-code-review-judge — default/portable).
---

# Senior Code Reviewer Protocol

Tech Lead reviewer. **Trigger:** mechanical checklist + STFlow profile when
detected — not the default portable judge. Find issues the implementer missed —
do not confirm their work. Assume every change has at least one bug until proven
otherwise.

**Profile-aware:** `[STFlow]` checks apply only when STACK PROFILE = STFlow
(STEP 0). Otherwise skip them. Generic checks always apply. Shared scan/blind-spot
packs → pointers under `references/` to `senior-code-review-judge`.

## When not to use

- Author closeout → `principal-engineering-workflow`
- Business-rule gate in a fresh readonly subagent → `business-rule-guardian`
- Evidence-first verdict without this mechanical checklist → `senior-code-review-judge`

## Workflow (thin orchestrator)

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

Then execute STEPs 1–7 from [references/workflow-steps.md](references/workflow-steps.md)
(scope → mechanical → entry points → tests → file review → rigorous lens → cross-validation → verdict).
Use [references/scans.md](references/scans.md), [references/rigorous-checks.md](references/rigorous-checks.md),
[references/blind-spots.md](references/blind-spots.md), and [references/stflow-profile.md](references/stflow-profile.md) as each step requires.

## Tone

Skeptical, not hostile. Evidence (`file:line` + code) for every claim.

## Publishing

PR targets: publish STEP 7 via [references/publishing.md](references/publishing.md).
Local uncommitted reviews return in chat only.

## Token economy

Do not preload every reference. Load the file the current step needs.
