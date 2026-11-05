# Judge report template

```text
=== SENIOR CODE REVIEW ===
Mode: LOCAL | REMOTE | PATCH-ONLY
Profile: <detected stack or generic>
Change: CODE | DOCS-ONLY | CONFIG/INFRA | MIXED
Risk: LOW | MEDIUM | HIGH | CRITICAL
Branch/PR: <reference or N/A>
Files reviewed: <N>
Round: <N>
Limitations: <none or explicit list>

INTENT:
<one sentence>

VERIFICATION:
- Lint: PASS | FAIL | NOT RUN | NOT AVAILABLE — <command/result>
- Typecheck: PASS | FAIL | NOT RUN | NOT AVAILABLE — <command/result>
- Tests: PASS | FAIL | NOT RUN | NOT AVAILABLE — <command/result and counts if available>
- Build: PASS | FAIL | NOT RUN | NOT AVAILABLE — <command/result>
- Security scans: <result or N/A>
- Other project checks: <result or N/A>

ENTRY POINT TRACE:
<relevant invariant and paths, or N/A with reason>

TEST ADEQUACY:
<behaviors, tests, what is actually proven, and meaningful gaps>

CRITICAL-SECURITY:
1. [F01] [path:line] `snippet` — evidence, impact, conditions, suggested direction

CRITICAL-CORRECTNESS:
1. [F02] [path:line] `snippet` — evidence, impact, suggested direction

IMPORTANT:
1. [F03] [path:line] `snippet` — evidence and why it matters

MINOR:
1. [F04] [path:line] `snippet` — concise rationale

OBSERVATIONS / PRE-EXISTING:
- <clearly labeled, evidence-backed item>

EXTERNAL RESEARCH:
- <official URL> — claim verified/refuted
- <none required>

VERDICT: APPROVED | APPROVED_WITH_NOTES | REJECTED | INCOMPLETE
REASON:
<short explanation tied to evidence>

FINDING LEDGER: (required when Round > 1 or when entering remediation)
- F01: RESOLVED | OPEN | DECLINED — <one-line evidence or rationale>
- F02: ...

REMEDIATION: (required when verdict is not APPROVED and Step 8a applies)
- Skill: principal-engineering-workflow
- Findings sent: F01, F02, ...
- Round status: INVOKING | WAITING_PARENT | ESCAPED_<reason> | COMPLETE_ROUND_N
- Next: re-review Steps 1–7 | stop (max rounds / escape) | human decision required
```

Omit empty finding sections or write `None`. Do not manufacture a finding just to fill the template. Every reported issue must have: stable finding id (`Fnn`); verified `path:line`; code excerpt or exact behavior; violated invariant, requirement, or demonstrated risk; impact and conditions; actionable fix direction.

On Round 1, assign finding ids when any material finding exists so Step 8a can hand a stable ledger to principal. On later rounds, preserve prior ids; add new ids only for genuine new findings.

If the tool supports inline PR comments, anchor only to changed lines accepted by the platform. Otherwise put the finding in the consolidated summary.
