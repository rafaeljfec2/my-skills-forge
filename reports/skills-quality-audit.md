# Skills quality audit

Date: 2026-10-23 (budget table refreshed after Akita-style remediation)  
Collection: `my-skills-forge` (20 skills under `skills/<domain>/<name>/`)  
Scope: audit plus remediation of P0/P1 budget and portability findings.

## Method

### Context budget

Same approximation as [`skills/ai-agents/context-budget-guard`](../skills/ai-agents/context-budget-guard/SKILL.md):

- `tokens ≈ bytes / 3.5`
- `SKILL.md`: soft 2,500 / hard 4,000
- `references/*.md`: soft 5,000 / hard 7,000

Measured with `python3 skills/ai-agents/context-budget-guard/scripts/audit_budget.py --root .`. The script discovers harness paths (`.cursor/skills`, `.claude/skills`) **and** the forge layout (`skills/*/*/SKILL.md`, `skills/*/*/references/**/*.md`).

### Qualitative axes

Activation, role clarity, progressive disclosure, portability, memory/cost, and prose consistency (English artifacts; PT-BR user replies only where declared).

### Curation lenses (Akita-informed)

Principles taken from [akitaonrails/my-skills](https://github.com/akitaonrails/my-skills) as **curation method only** (not as license or content to copy):

| Lens | Upstream source | Use in this audit |
|---|---|---|
| Personal skills carry foreign paths and assumptions | README | Flag STFlow / team / machine-global coupling |
| Inventory what stays outside the repo | README | Documented in forge README “Out of this repo / team-coupled” |
| Smallest useful form; “create nothing” can succeed | `reflect/SKILL.md` | Score review/PR overlaps |
| Frequency, cost, risk, stability, coverage | `reflect/SKILL.md` | Keep vs thin vs merge recommendations |
| Token economy: thin orchestrator, detail elsewhere | `fact-check/SKILL.md` / `security-audit` pattern | Thin injectable `SKILL.md`; detail in `references/` |
| Deletion test | `improve-codebase-architecture` | Does deleting the skill erase complexity or push it to many call sites? |
| Plain language; short obligations | `humanizer/AGENTS.md` | Description and MUST density |

Flat Akita layout was **not** adopted; domain folders stay.

---

## Executive summary

The collection is coherent: domains match roles, and **every** measured `SKILL.md` and `references/*.md` is under soft budget.

| Metric | Result |
|---|---|
| `SKILL.md` | **20 OK · 0 WARN · 0 FAIL** |
| `references/*.md` | **36 OK · 0 WARN · 0 FAIL** |
| Largest `SKILL.md` | `backend-engineering-expert` — 2,448 tok (soft 2,500) |
| Largest reference | `senior-code-review-judge/references/workflow-steps.md` — 4,750 tok (soft 5,000) |

Remediation applied: review skills thinned to Akita-style orchestrators; STFlow and step detail moved to `references/`; frontend SDD path retargeted; support docs under `references/`; README inventory added; `audit_budget.py` forge-aware.

Four skills remain `pending-review` in the catalog for license/merge reasons (not budget): `pr-creator-tr`, `pr-creator-outcoders`, `senior-code-review-judge`, `senior-code-reviewer-protocol`.

---

## Budget table (`SKILL.md`) — current

| Domain | Skill | Bytes | Tokens | Soft | Hard | Status |
|---|---|---|---|---|---|---|
| ai-agents | context-budget-guard | 7,304 | 2,086 | 2,500 | 4,000 | OK |
| architecture | software-architecture-expert | 5,228 | 1,493 | 2,500 | 4,000 | OK |
| design | ui-implement-figma | 5,761 | 1,646 | 2,500 | 4,000 | OK |
| devops | gh-create-pr | 3,829 | 1,094 | 2,500 | 4,000 | OK |
| devops | pr-creator-outcoders | 6,835 | 1,952 | 2,500 | 4,000 | OK |
| devops | pr-creator-tr | 5,693 | 1,626 | 2,500 | 4,000 | OK |
| engineering | backend-engineering-expert | 8,569 | 2,448 | 2,500 | 4,000 | OK |
| engineering | delphi-build | 5,028 | 1,436 | 2,500 | 4,000 | OK |
| engineering | error-plan-then-fix | 2,790 | 797 | 2,500 | 4,000 | OK |
| engineering | frontend-engineering-expert | 5,719 | 1,634 | 2,500 | 4,000 | OK |
| engineering | performance-observability-expert | 4,408 | 1,259 | 2,500 | 4,000 | OK |
| engineering | principal-engineering-workflow | 3,318 | 948 | 2,500 | 4,000 | OK |
| engineering | sdd-workflow | 1,338 | 382 | 2,500 | 4,000 | OK |
| productivity | job-search | 4,728 | 1,350 | 2,500 | 4,000 | OK |
| quality | business-rule-guardian | 3,408 | 973 | 2,500 | 4,000 | OK |
| quality | code-quality-standards | 7,343 | 2,098 | 2,500 | 4,000 | OK |
| quality | qa-automation-expert | 3,629 | 1,036 | 2,500 | 4,000 | OK |
| quality | senior-code-review-judge | 4,081 | 1,166 | 2,500 | 4,000 | OK |
| quality | senior-code-reviewer-protocol | 5,415 | 1,547 | 2,500 | 4,000 | OK |
| security | application-security-expert | 3,313 | 946 | 2,500 | 4,000 | OK |

### References (`references/*.md`)

Every file under soft (5,000). None at hard. Watch `workflow-steps.md` (~4,750) if it grows. Aggregate load still matters if an agent opens every reference at once (e.g. all five `sdd-workflow` refs); the orchestrator instructs “read only the phase/step needed”.

### Progressive disclosure

Support docs for `code-quality-standards` and `frontend-engineering-expert` live under `references/`. Scripts under `scripts/` are not injected as prompt text.

---

## Per-skill qualitative notes (current)

| Skill | Role fit | Notable notes | Keep posture |
|---|---|---|---|
| context-budget-guard | Clear; Do-NOT-use present | Forge layout scanned by `audit_budget.py` | Keep |
| software-architecture-expert | Clear specialist | Optional: add Do-NOT-use line | Keep |
| ui-implement-figma | Clear UI implementer | Token OK; 12-phase monolith (optional split) | Keep |
| gh-create-pr | Portable PR opener | Healthy size | Keep as default PR skill |
| pr-creator-tr | Team-TR PR + ADO/Teams | Team-coupled; pending-review | Keep for TR |
| pr-creator-outcoders | Team-Outcoders PR | Team-coupled; pending-review | Keep for Outcoders |
| backend-engineering-expert | Stack specialist | Near soft ceiling — prefer `references/` on next edits | Keep |
| delphi-build | Build specialist | Example Windows roots intentional | Keep |
| error-plan-then-fix | Error → plan → fix | Declares PT-BR user replies | Keep |
| frontend-engineering-expert | Stack specialist | Discovery → forge `sdd-workflow`; refs under `references/` | Keep |
| performance-observability-expert | Runtime perf/obs | Domain: engineering | Keep |
| principal-engineering-workflow | Author closes own work | PT-BR replies; links judge + protocol + security | Keep |
| sdd-workflow | Thin index + refs | Disclosure model; read one phase at a time | Keep |
| job-search | Session-profile job search | Portable | Keep |
| business-rule-guardian | Readonly subagent, business intent | Orchestrator ~973 tok; detail in `references/` | Keep |
| code-quality-standards | Hard limits + ESLint | Support md under `references/`; repo-local quality-check preferred | Keep |
| qa-automation-expert | Test strategy specialist | Clean | Keep |
| senior-code-review-judge | Verdict, no fixes | Orchestrator ~1,166 tok; pending-review license | Keep |
| senior-code-reviewer-protocol | Tech-lead checklist | Orchestrator ~1,547 tok; STFlow in `stflow-profile.md` | Keep |
| application-security-expert | AppSec specialist | Clean | Keep |

---

## Role clusters (Akita `reflect` scoring)

### Reviews (four skills)

| Skill | Frequency (expected) | Cost when activated | Risk if missing | Coverage overlap |
|---|---|---|---|---|
| principal-engineering-workflow | High (every delivery) | Low tokens | Medium | Author self-review |
| senior-code-review-judge | Medium (PR / pre-merge) | Low injectable; detail on demand | High if missing | Differs by “no fixes” + evidence verdict |
| senior-code-reviewer-protocol | Medium (STFlow / tech-lead) | Low–medium injectable | Medium outside STFlow | STFlow profile is the keep-reason |
| business-rule-guardian | Medium (gate before accept) | Low injectable + mandatory fresh subagent | High (intent drift) | Differs by isolation + business-rule mapping |

Keep all four roles. Do not merge judge and protocol while STFlow gating remains the differentiator. Do not fold guardian into judge: the mandatory clean subagent is the product.

### Pull requests (three skills)

| Skill | Audience | Recommendation |
|---|---|---|
| gh-create-pr | Any repo with a PR template | Default portable skill |
| pr-creator-tr | TR + ADO + Teams | Keep; team-coupled |
| pr-creator-outcoders | Outcoders + ADO | Keep; team-coupled |

---

## Findings by priority

### P0 / P1 — Done

1. Judge hard FAIL → thinned (~1,166 tok); detail in `references/workflow-steps.md` + `report-template.md`.
2. Guardian hard FAIL → thinned (~973 tok); detail in `references/workflow.md` + `output-and-severity.md`.
3. `audit_budget.py` forge-aware.
4. Frontend SDD path → forge `sdd-workflow`.
5. Protocol WARN → thinned (~1,547 tok); STFlow in `references/stflow-profile.md`.
6. Support markdown under `references/` for code-quality and frontend skills.
7. README “Out of this repo / team-coupled” section.

### P2 — Still open

8. **`backend-engineering-expert`** within ~50 tokens of soft; next edits via `references/`.
9. **`ui-implement-figma`**: optional phase split into `references/`.
10. Optional “Do NOT use …” on remaining specialist descriptions.
11. PT-BR reply rule only where declared (`principal-engineering-workflow`, `error-plan-then-fix`).
12. Catalog `pending-review` / unknown license before publication.
13. Watch `workflow-steps.md` (~4,750 tok) if it grows past soft 5,000.

---

## What is already in good shape

- Domain placement matches work.
- No `SKILL.md` or `references/*.md` soft/hard violations.
- `gh-create-pr` does not name removed skills.
- `principal-engineering-workflow` relative links resolve.
- Review sync scripts that treated `~/.cursor/skills/senior-code-reviewer` as source of truth are gone.
- Thin orchestrator pattern matches Akita token-economy curation.

---

## Recommended next work

1. Keep `backend-engineering-expert` under soft when editing (prefer `references/`).
2. Optional: split `ui-implement-figma` phases into `references/`.
3. Optional: add “Do NOT use” lines to remaining specialist descriptions.
4. Resolve `pending-review` licenses before publishing the collection.

## Verification

- Skills counted: **20** `SKILL.md` files under `skills/`.
- Current budget: **20 OK** for `SKILL.md`; **36 OK** for `references/*.md` (`audit_budget.py --root .`).
- Akita principles used as curation method; no Akita skill content imported.
- `test_audit_budget.py`: 18 tests OK. `_validate.py`: ALL VALIDATIONS PASSED.
