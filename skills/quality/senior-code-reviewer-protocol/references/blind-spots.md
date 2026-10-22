# Senior Code Reviewer — Common Blind Spots

The patterns reviewers miss most often. Check each one explicitly during STEP 5 and STEP 6.

1. **Guard added to `create()` but not `update()`** — always trace both CRUD paths
2. **Mock returns default value that makes new code a no-op** — the test "passes" but tests nothing
3. **New export added to a module but not added to test mocks** — causes runtime error in tests
4. **Function reads all files when it only needs one** — check if there's a direct/cached path
5. **Old files orphaned when references are updated** — dead code accumulates
6. **Prompt/instruction changes that contradict each other** — check all places the same concept is documented
7. **Duplicated logic across service and tool handler** — flag for extraction if types allow it
8. **`as Type` assertions bypass type checking** — use explicit variable typing (`const x: Type = ...`) instead of `expr as Type`. The compiler won't warn when the source type diverges from the target.
9. **`||` surviving in extracted/moved code** — when refactoring (extract function/file), convention violations in the ORIGINAL code get copied to the new location. Scan the FULL file, not just the diff additions.
10. **File line count exceeding limit after adding tests/helpers** — test files grow fast; always verify with `wc -l` after significant additions.
