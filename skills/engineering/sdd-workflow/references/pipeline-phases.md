# SDD Pipeline — 7 Phases (Detailed)

Canonical order: **Intake → SPEC → Review → Design → Test (Red) → Implementation (Green) → PR**

## Mandatory — No Phase Skipping

- **Every task that produces a diff** (code, tests, `*.md`, config, schema) MUST traverse all 7 phases in order.
- **No phase may be skipped, merged, shortened, or marked "N/A"** under any excuse ("it's a typo", "it's a small fix", "it's just docs", "the dev said hotfix") — unless the local rule defines a Trivial Fallback.
- **Zero `Edit` / `Write` on production files is permitted before**: (a) SPEC approved by the dev (AX-03), and (b) failing tests committed or presented (AX-06, Phase 5 Red).
- **Pure conversation** (questions, explanations, exploration that produce NO diff) is outside the pipeline. The moment a diff is proposed, the pipeline starts at Phase 1.
- **Test-only edits** (adding/updating a test for existing behavior) still require Phase 5 Red: the new/updated test MUST fail first against current production code, or the assertion is explicitly documented as "already passing — regression guard" in the SPEC.
- **Docs-only changes** follow the same 7 phases. SPEC and Review become lightweight in content (1–2 paragraphs) but are still **produced and approved**. Phase 5 Red may be replaced by an explicit "no-test justification" in the SPEC, approved by the dev.
- **Judging a phase "unnecessary" is a protocol violation**, not an optimization. If a phase feels redundant, STOP and ask the dev.

## Mandatory Phase Declaration

Every agent message that plans, proposes, or applies a diff MUST start with the current phase tag, exactly in this format:

```
[Phase N — Name]
```

Examples: `[Phase 0 — Project Discovery]`, `[Phase 1 — Intake]`, `[Phase 3 — Review]`, `[Phase 5 — Test (Red)]`, `[Phase 7 — PR]`.

Pure-conversation messages (no diff in this turn and no diff planned) use:

```
[No-Phase — Conversation]
```

**Note**: In any new project session, the FIRST diff-producing turn MUST be preceded by Phase 0 (Project Discovery). The agent cannot jump straight to Phase 1 without having read the project's briefing files.

The tag is the FIRST line of the message. Missing or incorrect tag = protocol violation.

## Phase 1 — Intake

**Goal**: Understand the task and produce structured intent.
**Gate**: Dev confirms intention.

Agent behavior:

1. Read the user request, goal, or work item — understand the **why** not just the **what**
2. Classify: feature / bug fix / refactor / schema migration / config / chore
3. Identify which workspace(s) / module(s) are affected
4. Map blast radius **mechanically** (AX-08):
   - Grep every function/type name to be created or modified — find ALL consumers codebase-wide
   - For new types: check shared packages first — import, never redefine
   - For modified interfaces: find ALL files that implement or depend on them
5. Challenge necessity: does an existing module/package already solve this?
6. Identify ambiguities — if any, STOP and ask dev before proceeding

**Output**: List of files to touch with justification, blast radius map, classification.

## Phase 2 — SPEC

**Goal**: Generate specification from intent + codebase analysis.
**Gate**: Automatic (proceeds to Review).

Agent behavior:

1. Analyze current codebase: schemas, services, modules, types, shared helpers
2. Anti-overengineering check: verify shared packages and existing utilities before creating new abstractions
3. Define: proposed changes, contracts, affected modules, edge cases, acceptance criteria
4. Verify every function/type in SPEC exists or is justified as new (AX-08)

## Phase 3 — Review

**Goal**: Validate SPEC for completeness and correctness.
**Gate**: **STOP — Dev approves SPEC** (AX-03). No code proceeds without approval.

Agent behavior:

1. Check SPEC completeness: are all affected files listed? Are edge cases covered?
2. Verify HARD RULE compliance (HR-01..06 + any local HRs in proposed code patterns)
3. Check for duplication: does similar logic already exist in shared packages or services?
4. Present findings to dev — SPEC only proceeds with explicit approval

## Phase 4 — Design

**Goal**: Architecture, implementation sequence, interfaces.
**Gate**: Dev confirms design.

Agent behavior:

1. Define implementation sequence (which files, which order — typically deepest to shallowest: schema → repository → service → controller → DTO → tests)
2. Design interfaces and contracts — `readonly` on all properties (HR-03)
3. Identify reuse opportunities from shared packages
4. For schema changes: plan migration in the project's migration tool/folder
5. For new endpoints: plan module, controller, service, DTOs in the project's conventional structure
6. Document architectural decisions with rationale

## Phase 5 — Test (Red Phase)

**Goal**: Write tests that FAIL because production code does not exist yet (AX-06).
**Gate**: Tests compile and FAIL (Red Phase confirmed). The failing output MUST be shown to the dev in a message tagged `[Phase 5 — Test (Red)]` — or committed on the branch — before Phase 6 begins.

Agent behavior:

1. Write tests FIRST — they MUST fail (AX-06)
2. Never modify a test to make it pass (AX-02, LIM-01)
3. Typed mocks — no `any` (AX-04, HR-02)
4. Test descriptions in English (HR-05)
5. Cover: happy path, edge cases, error scenarios, boundary conditions
6. Target the project's coverage threshold (HR-14, default 80% on new code)
7. Use the project's test runner (e.g., Vitest, Jest, node:test, pytest, etc.)
8. **Zero production `Edit`/`Write` is allowed in this phase.** Only test files and supporting test fixtures may be written.

## Phase 6 — Implementation (Green Phase)

**Goal**: Write production code that makes all Red Phase tests pass.
**Gate**: All tests pass + lint clean.

**Entry gate (MANDATORY):** Phase 6 begins ONLY after a prior message in the same session carries the tag `[Phase 5 — Test (Red)]` with visible failing-test evidence (runner output or commit hash), OR the SPEC contains a dev-approved `TDD-EXCEPTION` covering this change. Starting Phase 6 without one of these two conditions is a protocol violation (AX-01, AX-06).

Agent behavior enforces:

- HR-01: `??` for defaults
- HR-02: no `any`
- HR-03: `readonly` everywhere
- HR-04: ternary with `null` for conditional rendering
- HR-05: English in code, tests, identifiers, comments, logs
- HR-06: no redundant comments
- Cognitive complexity ≤ 15, one responsibility per function
- Guard clauses over nested conditionals
- Domain logic in services, not controllers
- Shared types in shared packages, not duplicated per app
- Node.js / language built-ins via explicit imports
- AX-07: divergence between code and SPEC is a bug — fix the code, not the SPEC

**Verification loop**: run tests → if fail → fix code → re-run → repeat until green or escalate.

## Phase 7 — PR

**Goal**: Create PR that passes all quality gates with independent reviewer approval.
**Gate**: PR created + reviewer APPROVED.

### Step 1 — Quality Gate (HR-13)

ALL must pass — no exceptions:

1. Typecheck (`tsc --noEmit` in TS, equivalent in other languages) per workspace
2. Lint (`pnpm lint` / `ruff` / `golangci-lint` / etc.)
3. Format check (`pnpm format --check` / `prettier --check` / equivalent)
4. Tests — full suite for modified workspaces, all green
5. Coverage check (per HR-14, default ≥ 80% on new code)
6. Build (production build, no errors)

If ANY check fails, return to Phase 6 and fix.

### Step 2 — Scope Check (HR-19)

Verify `git diff --name-only` contains ONLY task-related files. No out-of-scope changes.

### Step 3 — Independent Reviewer Subagent

See `reviewer-protocol.md` (in this same references folder) for the full reviewer protocol: spawn parameters, prompt template, checks, conversational rounds, and resume templates.

### Step 4 — Create PR

- **Title**: follow Conventional Commits (`feat:`, `fix:`, `chore:`, `refactor:`, etc.) or the project-specific convention defined in local rule
- **Branch**: follow the project-specific naming convention defined in local rule. Default fallback: `{type}/{short-slug}` (e.g., `feat/user-login`)
- **Body**: template with Description, Changes, Test Evidence, Reviewer Notes
- **Coverage**: per HR-14 (default ≥ 80% on new code)
- **Base branch**: as defined by the project (typically `main` or `develop`)

### Step 5 — Converge

Report to dev:

1. **What changed** — files touched, why each was modified
2. **Review outcome** — reviewer verdict, rounds needed, issues found and fixed
3. **SDD compliance** — AX/HR/LIM adherence summary
4. **Decisions made** — non-obvious choices with rationale
5. **Risks** — what could break, edge cases considered
