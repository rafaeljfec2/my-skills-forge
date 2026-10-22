# PR Template Section → Source Mapping

Use this table when filling `.github/pull_request_template.md` from session context.
Map each template heading to the best available evidence in the **current**
repository and session. Product-specific gate IDs from other repos are out of scope.

| Template section | Source |
|---|---|
| **Summary** | Session intent — 1-2 sentences (what + why) |
| **Context** — issue / related links | Links provided by the user; leave blank if none |
| **Context** — Spec / ADR / RFC | Paths to design docs produced in the session |
| **Type of change** | Commit prefix / change type actually used |
| **Process / compliance checklists** | Whatever the template lists; fill from completed session steps |
| **What changed** | Bullets from `git diff --stat` grouped by area |
| **How it was tested** | Tests actually run or added in the session |
| **Coverage / quality evidence** | Paste outputs the template asks for |
| **Risk & rollback** | Notes from design/implementation discussion |
| **Security & compliance** | Tick only items actually verified |
| **Performance impact** | Tick only paths exercised; remove if N/A |
| **Screenshots / demo** | Required when UI changed; otherwise remove and note "no UI change" |
| **Notes for reviewers** | Caveats, follow-ups, focus areas |

## Failure handling

| Failure | Action |
|---|---|
| `gh` not authenticated | Stop. Ask user to `gh auth login`. |
| Working tree dirty | Stop. Ask user to commit or stash. |
| Branch not pushed | Run `git push -u origin HEAD`, retry. |
| `gh pr create` returns "no commits between base and head" | Stop. Verify `git log <base>..HEAD` is non-empty. |
| Template file missing or malformed | Stop. Do not open a PR with an ad-hoc body. |
| Repository-required checks incomplete | Stop. Report the missing check. |
| Required review verdict missing or blocking | Stop. Finish review first. |
