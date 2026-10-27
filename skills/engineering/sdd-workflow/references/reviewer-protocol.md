# Phase 7 Step 3 — Independent Reviewer Adapter

**CRITICAL**: Review MUST run in a SEPARATE agent via the Task tool. The
implementing agent CANNOT review its own code. **Zero-bias** — the reviewer has
not authored the change.

## Default skill

Baseline default: **`senior-code-review-judge`**.

The subagent follows that skill's workflow and report template. This document is
only the SDD **adapter**: spawn, handoff package, verdict mapping, and rounds.

Local override: a project rule may require `senior-code-reviewer-protocol`
(e.g. STFlow). If unset, use `senior-code-review-judge`.

## Spawn the reviewer

```
subagent_type: "generalPurpose"
readonly: true
description: "Independent code review — Round 1 (senior-code-review-judge)"
```

Save the returned `agentId` for resume rounds.

## Prompt template (handoff package)

```
You are an independent reviewer. You have NOT authored this change.
Follow the catalog skill `senior-code-review-judge` (its SKILL.md and
references). Do not implement fixes unless separately requested.

## Claim (from approved SPEC)
<exact Claim text>

## Evidence path (from SPEC)
- Success type: <test|build|lint|command|manual|oracle>
- Path: <how the claim was to be established>
- Budget / affordance notes: <if any>

## Actual evidence result
<command output, paths, or manual notes that should establish the Claim>

## What was implemented
<one paragraph describing the goal>

## Files modified
<output of git diff --name-only>

## Full diff
<output of git diff>

## Build & test evidence (HR-13)
<typecheck, lint, format, test, coverage, build>

## SDD Compliance (also verify)
- AX-01..08
- HR-01..06, HR-13, HR-14, HR-19 (+ project-specific HRs)
- LIM-01..10

If Claim or the Evidence block is missing from this package, emit
CLARIFICATION_NEEDED — do not APPROVE as a favor.

Return the judge report with an explicit SDD loop verdict mapping
(APPROVED | NEEDS_FIX | CLARIFICATION_NEEDED) per the adapter table.
```

## Verdict mapping (judge → SDD loop)

| Judge outcome | SDD loop response | Action |
| --- | --- | --- |
| No material CRITICAL / IMPORTANT | `APPROVED` | Create PR |
| CRITICAL or IMPORTANT findings | `NEEDS_FIX` | Fix, re-run HR-13, resume with Template B |
| Missing claim/evidence package, or unclear design context | `CLARIFICATION_NEEDED` | Answer via Template A |
| Only MINOR / NIT after round 3 | Treat as proceed | Create PR; report remaining nits to the developer |

Legacy labels CRITICAL/HIGH in older notes map to CRITICAL/IMPORTANT.

## Conversational review — max 3 rounds (default)

| Response | Action |
| --- | --- |
| `APPROVED` | Create PR |
| `CLARIFICATION_NEEDED` | Answer via resume (Template A) |
| `NEEDS_FIX` | Fix code, re-run quality gates, resume (Template B) |

Trivial fallback: **max 1 round** — see [trivial-fallback.md](trivial-fallback.md).

### Template A — Resume for clarification

```
Round N — Clarification response.

## Your question
<original CLARIFICATION_NEEDED item from the reviewer>

## Answer
<explanation with code references, design rationale, or additional context>

Continue your review with this additional context.
Emit updated findings for any items that were pending clarification.
```

### Template B — Resume for fix validation

```
Round N — Re-validation after fixes.

## Issues fixed
<list each issue ID with what changed and file:line references>

## New diff (only the fixes)
<output of git diff for the fix commits>

## Updated build evidence
<quality gates results after fixes>

## Claim evidence (if affected)
<re-run of SPEC success-type evidence if the fix touched the claim path>

Re-validate ONLY the items you flagged. Do NOT re-review the entire diff.
Emit updated verdict (APPROVED | NEEDS_FIX | CLARIFICATION_NEEDED).
```

## Loop control

- Round 1: Initial review (spawn)
- Round 2: Clarification response OR first fix validation (resume)
- Round 3: Final fix validation if needed (resume)

After 3 rounds: if `APPROVED` or only MINOR/NIT → create PR. If CRITICAL or
IMPORTANT remain → **STOP and report to the developer**.
