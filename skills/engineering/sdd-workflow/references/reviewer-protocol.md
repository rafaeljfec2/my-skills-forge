# Phase 7 Step 3 — Independent Reviewer Subagent Protocol

**CRITICAL**: Review MUST be executed by a SEPARATE agent via the Task tool. The implementing agent CANNOT objectively review its own code. **Zero-bias** requirement — the reviewer has never seen the code before.

## Spawn the reviewer

```
subagent_type: "generalPurpose"
readonly: true
description: "Independent code review — Round 1"
```

Save the returned `agentId` — you need it for resume rounds.

## Prompt template

```
You are an independent code reviewer. You have NOT seen this code before.
Read the SDD protocol rule(s) in .cursor/rules/ and follow the reviewer checklist.

## What was implemented
<one paragraph describing the goal>

## Files modified
<output of git diff --name-only>

## Full diff
<output of git diff>

## Build & test evidence
<HR-13 results: typecheck, lint, format, test, coverage, build>

## SDD Compliance
- Verify AX-01..08 compliance
- Verify HR-01..06, HR-13, HR-14, HR-19 compliance (+ any project-specific HRs)
- Verify LIM-01..10 compliance

Execute the FULL review checklist.
Return findings in structured format with verdict.

If any design decision is unclear or you lack context to evaluate an item,
emit CLARIFICATION_NEEDED instead of assuming it is a bug.
```

## Reviewer checks

- **AX/HR/LIM compliance**: verify axiom, hard rule, and limit adherence
- **Structural**: file size (~300 ideal / ~500 ceiling), complexity (15 max), duplication
- **Type safety**: no `any`, no unsafe casts, `readonly`, explicit return types
- **Security**: no secrets in code, parameterized queries, validated inputs, tenant isolation if applicable
- **Architecture**: domain logic in services, shared types in shared packages, no deep relative imports across workspaces
- **Integration completeness**: every new parameter has a call site, no dead exports, no duplicate functions, shared types not redefined locally
- **Regression risk**: existing tests for modified modules still pass
- **Call-graph tracing**: grep all callers of modified functions, verify signature compatibility

## Conversational review — max 3 rounds (default)

| Response                       | Action                                                       |
| ------------------------------ | ------------------------------------------------------------ |
| `APPROVED` (no CRITICAL/HIGH)  | Create PR                                                    |
| `CLARIFICATION_NEEDED`         | Answer via resume (template A)                               |
| `NEEDS_FIX` (CRITICAL or HIGH) | Fix code, re-run quality gates, resume reviewer (template B) |

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
<list each issue ID (C1, H1, etc.) with what was changed and file:line references>

## New diff (only the fixes)
<output of git diff for the fix commits>

## Updated build evidence
<quality gates results after fixes>

Re-validate ONLY the items you flagged. Do NOT re-review the entire diff.
Emit updated verdict.
```

## Loop control

- Round 1: Initial review (spawn)
- Round 2: Clarification response OR first fix validation (resume)
- Round 3: Final fix validation if needed (resume)

After 3 rounds: if APPROVED or only LOW/NIT items → create PR. If CRITICAL/HIGH remain → **STOP and report to dev**.
