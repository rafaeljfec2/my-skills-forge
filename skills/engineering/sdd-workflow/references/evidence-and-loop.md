# Evidence Path, Typed Green Loop, and Deepwork

Forge-owned procedure detail for Spec-Driven delivery. Method inspiration only —
no upstream skill text. Read this when building or closing the SPEC evidence
block, running Phase 6, deciding deepwork, or handing off to Phase 7 review.

## 1. Evidence path (SPEC — mandatory)

Every non-trivial SPEC MUST end with an **Evidence** block. A SPEC without this
block is **incomplete** and MUST NOT pass Phase 3 (Review).

| Field | Required | Content |
| --- | --- | --- |
| **Claim** | Yes | The behavior that must become true after the change |
| **Success type** | Yes | One of: `test`, `build`, `lint`, `command`, `manual`, `oracle` |
| **Evidence path** | Yes | How *this* system can establish, limit, or refute the claim |
| **Budget** | Yes | Minimum non-duplicative evidence that covers the claim and important boundaries |
| **Affordance?** | If needed | Smallest capability that makes decisive state controllable/observable when truth is too indirect today; state temporary vs durable |

For docs-only or approved no-test cases, still state Claim + Success type + path
(e.g. `manual` review of rendered docs) or the SPEC's `TDD-EXCEPTION` /
no-test justification — never omit the block.

Trivial fallback: replace this table with **1–2 lines** (see
[trivial-fallback.md](trivial-fallback.md)).

## 2. Anti-theater (Green gate)

Phase 6 closes **only** when evidence of the SPEC's **success type** establishes
the Claim.

- A generic green suite that does not exercise the Claim is **not** a pass.
- HR-13 still runs in Phase 7; it does not replace Claim-scoped evidence.
- If the planned path cannot establish the Claim, STOP and escalate to the developer
  (update path, affordance, or SPEC) — do not redefine success silently.

## 3. Typed green loop (Phase 6)

1. Criterion = SPEC **Success type** (+ Evidence path).
2. Execute production changes allowed in Phase 6.
3. Run the Claim-scoped evidence.
4. If fail → fix production code only (AX-02, LIM-01) → re-run.
5. **Max 3 attempts.** On the third failure, escalate to the dev: do not invent a
   fourth hack, weaken tests, or change the Claim without re-approval.
6. Record attempt count and last evidence output in the session before Phase 7.

Red→Green (AX-06) remains mandatory unless a dev-approved `TDD-EXCEPTION`
covers the change.

## 4. Deepwork brake (optional, rare)

Set `DEEPWORK=yes` in Intake/Design **only** when **at least two** of these are
true:

1. Cross-module change, migration, or auth / money / sensitive-data surface
2. More than one independent delivery boundary
3. Partially shipping would be unsafe or incoherent

Otherwise use the normal pipeline. Do not enable deepwork merely because many
files are touched.

When `DEEPWORK=yes`:

- Phase 4 splits work into delivery boundaries with gate order and ownership
- After each boundary: focused validation + a bounded review gate before the next
- Full `senior-code-review-judge` runs **once** at Phase 7 — not after every
  sub-phase
- Persist boundary status in the SPEC or a project-local note; do not invent a
  second protocol

## 5. Phase 7 handoff to the judge

Minimum package for the independent reviewer (see
[reviewer-protocol.md](reviewer-protocol.md)):

1. Claim
2. Evidence path (from SPEC)
3. Actual evidence result (command output, paths, or manual notes)
4. Diff (`git diff` / name-only list)
5. HR-13 results

If Claim (or the Evidence block) is missing from the package, the reviewer MUST
emit `CLARIFICATION_NEEDED` — never `APPROVED` as a favor.

## 6. Trivial changes

Use the one-line evidence form and single-round judge rules in
[trivial-fallback.md](trivial-fallback.md).
