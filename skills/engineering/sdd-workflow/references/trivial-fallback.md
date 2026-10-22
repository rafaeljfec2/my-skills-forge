# Optional — Trivial Fallback

This baseline allows projects to opt into a Trivial Fallback for genuinely small changes. **A project may disable or override this in its local rule.** If no local rule says otherwise, the fallback below applies.

## Trivial qualification (ALL must be true)

- Touches AT MOST 1 source file (lockfiles, `package.json`, snapshots and auto-generated configs do NOT count IF they are direct side effects of the single change)
- No public-behavior change (API, HTTP contract, user-visible render, DB schema, queue event, structured log format)
- No NEW dependency. Patch-bump of an existing dep counts as trivial; minor/major bump does NOT
- No DB migration (even additive)
- No change in a module classified as CRITICAL by the local rule

## Examples that qualify

- Typo fix in UI string literal or comment (1 file)
- Trivial config constant tweak (e.g., timeout 5s → 10s)
- Patch bump of existing dep with no published API change
- JSDoc / non-obvious-intent comment adjustment
- Manual import reordering / formatting

## Phase map for trivials

| Phase                     | Trivial?            | Detail                                                                                                                                                         |
| ------------------------- | ------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1. Intake                 | MANDATORY           | 1-line classification + affected file                                                                                                                          |
| 2. SPEC                   | OMITTED             | Replaced by short description (1-2 lines) in PR/commit                                                                                                         |
| 3. Dev Review             | OMITTED             | No prior approval needed                                                                                                                                       |
| 4. Design                 | MANDATORY (reduced) | Identify file + pointed change (1-3 lines explaining "what" and "why")                                                                                         |
| 5. Test                   | MANDATORY           | Smoke test or focused test covering the change. AX-02 applies (test sacred)                                                                                    |
| 6. Implementation (Green) | MANDATORY           | Minimum code + run local quality gates                                                                                                                         |
| 7. PR + Reviewer          | MANDATORY (reduced) | Full quality gates + reviewer subagent with focused checklist. Max **1 round** (if NEEDS_FIX persists = it wasn't trivial — escalate and follow full pipeline) |

## Always enforced (even in trivials)

- HR-01..06 + any local HRs
- LIM-01..10
- AX-02 (test sacred), AX-04 (no any), AX-05 (review required), AX-08 (verify)
- Quality gates (ALL)

## When in doubt about triviality

Treat as NON-trivial and follow the full pipeline. The reviewer can reclassify as trivial if it judges the full pipeline excessive.
