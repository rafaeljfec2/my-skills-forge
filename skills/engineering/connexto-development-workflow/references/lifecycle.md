# Lifecycle

Checkpoint: `.connexto/runs/<demand-id>/state.json`. Reload it after every interruption. The chat transcript is not the state.

Operators invoke the skill in chat; see [operator-usage.md](operator-usage.md). Agents run `cdw.py` from the forge checkout:

```bash
python3 skills/engineering/connexto-development-workflow/scripts/cdw.py <command>
# or from my-skills-forge root after pnpm link:apply — same path under skills/engineering/…
```

Public transitions use `transition`. Gated transitions below are refused on `transition` and run only through the named operation.

## Edges

| Edge | Reason | Role | Operation | Success | Failure |
|---|---|---|---|---|---|
| PENDING → INTAKE | `start` | orchestrator | `transition` | `brief.md` and the project snapshot exist | stay PENDING |
| INTAKE → RESEARCH | `intake_complete` | orchestrator | `transition` | brief has problem, outcome, and success criteria | stay INTAKE; HIGH risk with no `start_high_risk` approval parks in WAITING_APPROVAL |
| RESEARCH → PLAN | `research_complete` | researcher, orchestrator | `transition` | `research.md` has Facts, Hypotheses, Gaps, Evidence, and `Implemented: no` | stay RESEARCH |
| RESEARCH → RESEARCH | `insufficient_research` | researcher, orchestrator | `transition` | the gap is recorded in `evidence/execution.jsonl` | stay RESEARCH |
| PLAN → IMPLEMENT | `plan_accepted` | planner, orchestrator | `transition` | `spec.md` has `## Behavior`, `plan.md` has `## Acceptance criteria`, `tasks.md` has an open task | stay PLAN; an isolated git branch is created when the repo is a git checkout |
| PLAN → PLAN | `inconsistent_plan` or `scope_change` | planner, orchestrator | `transition` | the plan is still the current artifact | stay PLAN |
| IMPLEMENT → PLAN | `scope_change` | developer, planner, orchestrator | `transition` | validation flags are cleared | stay IMPLEMENT |
| IMPLEMENT → VALIDATE | `implementation_ready` | developer, orchestrator | `validate` | developer id and `developer/report.json` or successful implement hook | stay IMPLEMENT |
| VALIDATE → REVIEW | `validation_passed` | developer, orchestrator | `validate` | every required command exited 0 and was appended to `evidence/commands.jsonl` | record the failure |
| VALIDATE → IMPLEMENT | `validation_failed` | developer, orchestrator | `validate` | failure count is below `quality.max_validate_attempts` | stay VALIDATE only if the process died mid-command; call `validate` again |
| VALIDATE → FAILED | `attempts_exhausted` | developer, orchestrator | `validate` | the attempt counter reached the configured limit | terminal FAILED |
| REVIEW → DELIVERY | `review_clear` | reviewer | `review` or `run-judge` | reviewer id and session differ from developer; no blocking findings | stay REVIEW |
| REVIEW → IMPLEMENT | `review_defect` | reviewer | `review` | a blocking finding asks for another implementation pass | validation flags are cleared |
| REVIEW → PLAN | `review_solution_failure` | reviewer | `review` | a blocking finding sets `return_to` to PLAN | validation flags are cleared |
| DELIVERY → MEMORY | `delivery_recorded` | orchestrator | `transition` | `deliver` wrote `delivery.md` | stay DELIVERY |
| MEMORY → DONE | `memory_recorded` or `memory_skipped` | orchestrator | `memory-sync`, `memory-ack`, or `memory-skip` | remote memory confirmed when sync commands are set; else ack path after real write; or skip when disabled | stay MEMORY |

## Auxiliary states

| Entry | Role | Success | Failure |
|---|---|---|---|
| WAITING_APPROVAL | orchestrator requests; a different actor id approves | `approve` resumes the parked transition or restores the previous state | the requester cannot approve |
| BLOCKED | orchestrator `block` | `unblock` restores the same state | missing resume status stays blocked |
| FAILED | orchestrator `fail`, or the validation attempt limit | terminal | a new demand id is required |
| CANCELLED | orchestrator `cancel` | terminal | a new demand id is required |

Protected actions (`protect`) also park in WAITING_APPROVAL. They do not run the action. This MVP does not merge, publish, deploy, or change infrastructure.

Every successful move appends one JSON line to `evidence/execution.jsonl` with the demand id, status, reason, and actor id. Command stdout and stderr are redacted before they reach `evidence/commands.jsonl`.
