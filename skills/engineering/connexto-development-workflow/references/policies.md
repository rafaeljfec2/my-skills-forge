# Policies

Autonomous work may read the tree, write run artifacts, create a work branch, edit within the approved scope, run the configured commands, commit on that work branch when `git.allow_commit` is true, and request review.

## Protected actions

`cdw.py protect --action <name>` parks the run. The engine does not perform the action after approval. Approval only records that a different actor id accepted the request. Carrying it out needs a later, explicit operation outside this MVP.

- `merge_protected`
- `production_publish`
- `destructive_database`
- `infrastructure_change`
- `secret_rotation`
- `irreversible`
- `permission_change`

HIGH demands also wait for `start_high_risk` before RESEARCH. The actor who requested the wait cannot approve it.

## Git

- `git.isolated_branch`: entering IMPLEMENT checks out `connexto/<demand-id>` when the target is a git repository. A non-git target is recorded and does not fail the transition.
- `git.allow_commit`: `commit` is refused when this is false, when the current branch is `git.base_branch`, or when a path or its text looks credential-shaped.
- Commit paths are explicit. `.connexto/`, `.env`, `.git`, `credentials.json`, and `*.pem` / `*.key` are refused.
- The engine reads `user.email`. It does not write git config. When no email is set, the commit command passes a temporary identity only for that process.

## Secrets

Do not put credentials in `connexto.project.json`, prompts, artifacts, or commit messages. Assignment-shaped tokens, AWS access-key ids, and private-key blocks are rejected in config and redacted in command logs.

## Validation

At least one of `require_tests`, `require_lint`, `require_typecheck`, or `require_build` must be true, and the matching command must be a non-empty string. Other commands stay null. The engine does not invent `pnpm`, `npm`, or a language.

`quality.max_validate_attempts` counts failed validation passes. The next failed pass at the limit moves the run to FAILED.

## Release claims

`delivery.md` always records merge, production publish, and deploy as `not performed`. Prose that says the change was merged to main or master, published to production, or deployed to production is refused. This MVP has no merge or deploy operation.
