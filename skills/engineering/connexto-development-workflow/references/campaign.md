# Campaign queue

One campaign runs one sprint at a time. The parser reads the **root campaign execution plan** as its ordered queue source. Each registered sprint must contain exactly T1, T2, T3, and T4. Campaign state is `.connexto/campaigns/<id>/state.json`. Demand state stays in `.connexto/runs/<id>/state.json`.

Keep these artifacts distinct:

- **Root campaign execution plan:** the parser input that registers sprint IDs, branches, task labels, and queue order. It is the only parser input; a per-sprint plan document does not register or reorder a sprint.
- **Per-sprint execution plan:** the detailed, approvable plan for one queue item. Its structure and language are defined by the target repository's own `AGENTS.md` and always-applied rules. Use the exact canonical template designated there.
- **Demand-level `plan.md`:** the generic SDD artifact stored in `.connexto/runs/<id>/`, created from this skill's `templates/plan.md`. It is not a substitute for the per-sprint execution plan.

The legacy `references/sprint-execution-plan.md` is retained only as a compatibility notice. It is not an active authoring template. Do not use its structure or language instruction when preparing a campaign sprint plan. If the target project has no canonical per-sprint template, mark the dependent plan `BLOCKED` instead of inventing one.

`CAD-NNN` is a `FEATURE` id. Omitted risk stays the FEATURE floor, `MEDIUM`. Do not pass a lower risk.

Sprint **Branch** values use a conventional prefix and a lowercase slug, for example `feat/cad-000-foundation`, `fix/bug-012-null-check`, or `docs/readme-index`. Allowed prefixes: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`, `hotfix`.

## Commands

- `campaign-init` reads the root campaign execution plan and records the operator attestation. It does not approve a language SPEC.
- `campaign-status` reloads the checkpoint.
- `campaign-open-sprint` fetches `origin` and refuses sprint N+1 until the previous sprint head is on `origin/<integration>`.
- `campaign-bind-branch` stores the feature branch before `plan_accepted` when `git.isolated_branch` is true.
- `campaign-record-review` stores `pre-pr` or `post-pr` against the current `HEAD`.
- `campaign-commit` commits on the active feature branch. `cdw commit` still obeys `git.allow_commit`.
- `campaign-open-pr` and `campaign-merge` accept only verdict `APPROVED` for the current `HEAD`, with no finding in `BLOCKING_SEVERITIES` for the demand risk. The post-PR actor and session must differ from the pre-PR pair. The merge target is the integration branch and is never the release branch.
- `campaign-register-pr` binds an already-created pull request to the active sprint when `gh pr view` reports `OPEN` or `MERGED`, the PR base is the integration branch, and the head branch is not protected. For `MERGED` PRs, checks must be present and green. It records `pr_number`, `pr_url`, and `branch` from the PR head ref. It does not create a PR, merge, set `head_sha`/`merge_sha`, clear `current_sprint`, or open the next sprint. Use this when a PR was opened outside `campaign-open-pr` so a later `campaign-reassociate-head` can match the checkpoint.

A local `merged` flag is not acceptance. `campaign-reconcile` reads the remote ref and, when a pull request number is known, `gh pr view`. It does not replace a stored `head_sha`.

- `campaign-reassociate-head` rebinds only the active sprint when `gh pr view` reports `MERGED`, the requested head equals both the PR head and `origin/<branch>`, that head is contained in the requested merge commit, and that merge commit is on `origin/<integration>`. Checks must be present and green. It records `head_sha`, `merge_sha`, and `status=merged`, then clears `current_sprint`. It does not merge, push, check out a branch, or open the next sprint. `campaign-reconcile` still has to set `merge_on_integration`.

## Execution plan

A sprint or governance-unblock execution plan uses the target repository's canonical sprint-plan template. Cursor Plan mode stays read-only. The approved plan becomes the Connexto PLAN artifacts; it does not open the sprint by itself. Do not author from the legacy [sprint-execution-plan.md](sprint-execution-plan.md) notice.
