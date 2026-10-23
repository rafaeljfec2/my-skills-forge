# Judge report template

```text
=== SENIOR CODE REVIEW ===
Mode: LOCAL | REMOTE | PATCH-ONLY
Profile: <detected stack or generic>
Change: CODE | DOCS-ONLY | CONFIG/INFRA | MIXED
Risk: LOW | MEDIUM | HIGH | CRITICAL
Branch/PR: <reference or N/A>
Files reviewed: <N>
Round: <N or unknown>
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
1. [path:line] `snippet` — evidence, impact, conditions, suggested direction

CRITICAL-CORRECTNESS:
1. [path:line] `snippet` — evidence, impact, suggested direction

IMPORTANT:
1. [path:line] `snippet` — evidence and why it matters

MINOR:
1. [path:line] `snippet` — concise rationale

OBSERVATIONS / PRE-EXISTING:
- <clearly labeled, evidence-backed item>

EXTERNAL RESEARCH:
- <official URL> — claim verified/refuted
- <none required>

VERDICT: APPROVED | APPROVED_WITH_NOTES | REJECTED | INCOMPLETE
REASON:
<short explanation tied to evidence>
```

Omit empty finding sections or write `None`. Do not manufacture a finding just to fill the template. Every reported issue must have: verified `path:line`; code excerpt or exact behavior; violated invariant, requirement, or demonstrated risk; impact and conditions; actionable fix direction.

If the tool supports inline PR comments, anchor only to changed lines accepted by the platform. Otherwise put the finding in the consolidated summary.
