# Roles

One runtime may play every role. The engine still refuses a role that does not own the artifact or the edge. Actor ids are strings. They are not operating-system identities. A review is independent only when the reviewer id differs from the developer id and, for an SDD delivery, when `senior-code-review-judge` runs in a fresh readonly subagent.

| Role | Owns | Must not |
|---|---|---|
| orchestrator | init, intake, delivery, memory ack, block, cancel, fail, approval of someone else's request | submit the review for a demand whose developer id is this same actor |
| researcher | `research.md` | edit product code or record `Implemented: yes` |
| planner | `spec.md`, `plan.md`, `tasks.md` | implement the change |
| developer | implementation note, optional `commands.implement` hook, validation request, work-branch commit | approve the review |
| reviewer | `review.json` | be the developer id; edit the product tree while acting as reviewer |

## Review payload

`cdw.py review --file review.json`

```json
{
  "summary": "What was checked against the acceptance criteria.",
  "findings": [
    {
      "severity": "important",
      "file": "src/app.py",
      "location": "save_order",
      "rationale": "The error path is untested.",
      "return_to": "IMPLEMENT"
    }
  ]
}
```

Severity is `critical`, `blocking`, `important`, or `minor`. `return_to` is `IMPLEMENT` or `PLAN`. A PLAN return on a blocking finding leaves REVIEW for PLAN.

Blocking severities:

| Risk | Blocks delivery |
|---|---|
| LOW | `critical`, `blocking` |
| MEDIUM | `critical`, `blocking`, `important` |
| HIGH | `critical`, `blocking`, `important`, and `start_high_risk` must already be approved |

## Defaults by demand type

| Type | Id prefix | Default risk |
|---|---|---|
| FEATURE | `FEAT-001` | MEDIUM |
| BUGFIX | `BUG-001` | LOW |
| REFACTOR | `REFACTOR-001` | MEDIUM |
| HOTFIX | `HOTFIX-001` | HIGH |
| TECHNICAL_DEBT | `DEBT-001` | LOW |

An explicit risk may raise the default. It may not lower it.
