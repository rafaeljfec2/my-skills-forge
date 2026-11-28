# Sprint execution plan

Fill this template when Cursor Plan mode, or the Connexto PLAN phase, produces the execution plan for one campaign sprint or one governance unblock. The filled plan is the approvable artifact. A free-form design does not satisfy this template.

Read [campaign.md](campaign.md) for the queue, the sprint grammar, and the `cdw.py` commands. This template does not add a workflow and does not name a command that file does not list.

## Output rules

- Write the plan prose in Brazilian Portuguese.
- Keep identifiers, task titles, status tokens, paths, SHAs, and commands in English.
- Use exactly four tasks, `T1` through `T4`, with titles the campaign parser can register.
- Mark any baseline not re-read from the repository as `hypothesis`.
- In Plan mode, stay read-only. Do not open the feature branch, run the sprint, or edit campaign state.
- If the repository requires an authorization or a `cdw.py` command that is not present, end section 3 as `BLOCKED` and name the missing piece. Do not invent a sprint id, branch, reviewer, or command.

## Class

Choose one class in section 1.

| Class | Mission | Plan success | Stays frozen |
| --- | --- | --- | --- |
| `product-gate` | Decide whether the normative contract is satisfied | Sprint may be `DONE` while the gate stays `ACCEPTED` or `PARTIAL` | The next phase and frozen language semantics |
| `governance-unblock` | Make the next sprint eligible in the existing queue | `REGISTERED-PENDING` | Execution of that sprint and of every later sprint |

## Required sections

Use these headings, in this order.

### 1. Authorization

State the single change this plan may perform. In the same section, list the branches, sprints, phases, state files, and commands this authorization leaves untouched.

### 2. Baseline hypothesis

Record the reported tip SHA, queue, working tree, and line counts. Label each item `verified` or `hypothesis`. The first execution action is to re-read the repository.

### 3. Preflight

List the files, symbols, and rules execution must read before a branch or a diff. Each item names the evidence that answers it. A missing compliant mechanism ends the plan as `BLOCKED`.

### 4. Conjunctive blockers

Name each independent blocker. For each one, state the proof that does not close it. The plan succeeds only when every blocker is closed.

### 5. Sensors

List the evidence categories the sprint must keep distinct. Bind every measurement to the candidate SHA. State how a filtered test, a skipped workflow, and a reused historical count appear in the report.

### 6. Observers

Name each independent role and require a fresh context. For `product-gate`, keep audit quality and the product recommendation as separate axes.

### 7. Automaton

State the initial status, each transition, and the status that does not change. `NEEDS_FIX` returns to the evidence and requests a new observer. `STOP` preserves the evidence and does not promote the gate.

### 8. History

State which records stay immutable. Describe the queue change as an insertion or another supported transition. Require the update to go through a documented `cdw.py` command and to be safe to repeat.

### 9. Delivery

Record the sequence: one branch, one SPEC, independent SPEC review, validator, CI on the candidate SHA, pre-merge judge, merge, post-merge judge, checkpoint re-read. Map the sections to Connexto artifacts after approval:

| Plan section | Connexto artifact |
| --- | --- |
| 1–3 | `research.md` with `Implemented: no` |
| 4–7 | `spec.md` with `## Behavior` |
| 8 and T1–T4 | `tasks.md` with exactly four open items `- [ ]` |
| 9–10 | `plan.md` with `## Acceptance criteria` |

The planner does not approve the SPEC. Acceptance of this Cursor plan does not replace the independent SPEC review required before `plan_accepted`.

### 10. Report and status block

List the report fields execution must fill. Close with a status block whose tokens come from the campaign vocabulary. Leave an unrun field as not run.

## Plan todos

The Cursor plan todo list contains exactly these four items and no others:

1. `T1 —` first parser-recognized task
2. `T2 —` second parser-recognized task
3. `T3 —` third parser-recognized task
4. `T4 —` fourth parser-recognized task

Put tests, CI, audit, and closeout inside the matching task. Do not add a fifth todo.
