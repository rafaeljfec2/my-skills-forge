# Campaign queue

One campaign runs one sprint at a time. The queue is parsed from the campaign plan. Each sprint must contain exactly T1, T2, T3, and T4. Campaign state is `.connexto/campaigns/<id>/state.json`. Demand state stays in `.connexto/runs/<id>/state.json`.

`CAD-NNN` is a `FEATURE` id. Omitted risk stays the FEATURE floor, `MEDIUM`. Do not pass a lower risk.

Sprint **Branch** values use a conventional prefix and a lowercase slug, for example `feat/cad-000-foundation`, `fix/bug-012-null-check`, or `docs/readme-index`. Allowed prefixes: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`, `hotfix`.

## Commands

- `campaign-init` reads the plan and records the operator attestation. It does not approve a language SPEC.
- `campaign-status` reloads the checkpoint.
- `campaign-open-sprint` fetches `origin` and refuses sprint N+1 until the previous sprint head is on `origin/<integration>`.
- `campaign-bind-branch` stores the feature branch before `plan_accepted` when `git.isolated_branch` is true.
- `campaign-record-review` stores `pre-pr` or `post-pr` against the current `HEAD`.
- `campaign-commit` commits on the active feature branch. `cdw commit` still obeys `git.allow_commit`.
- `campaign-open-pr` and `campaign-merge` accept only verdict `APPROVED` for the current `HEAD`, with no finding in `BLOCKING_SEVERITIES` for the demand risk. The post-PR actor and session must differ from the pre-PR pair. The merge target is the integration branch and is never the release branch.

A local `merged` flag is not acceptance. `campaign-reconcile` reads the remote ref and, when a pull request number is known, `gh pr view`.
