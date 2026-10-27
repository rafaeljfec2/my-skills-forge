# Prerequisites, commands, and create steps

Detail for `gh-create-pr`. Load only when executing the matching workflow step.

## Prerequisites

- `gh auth status` returns OK (if not, ask the user to run `gh auth login`)
- `git status` shows a clean working tree (no uncommitted local changes)
- Required checks documented by the current repository are complete
  (tests, lint, review verdict, linked issue/spec — whatever the template asks)
- If the repository requires an independent review skill before PR open,
  that review must already be done with an approvable verdict

If any prerequisite required by the current repository is missing → STOP,
report what is missing, and do not open the PR.

## Inputs

- `base`: target branch (default `main`, or the repo default)
- `head`: current branch (must already be pushed to origin)
- session context needed to fill the template sections

## Step 1 — Verify prerequisites

```bash
gh auth status
git status --porcelain
git rev-parse --abbrev-ref HEAD
```

- If `gh` is not authenticated → instruct the user to run `gh auth login` and stop.
- If the working tree is dirty → stop. Commits must already be in place.
- If the current branch equals the base branch → stop.

## Step 2 — Push the branch (if not yet pushed)

```bash
git push -u origin HEAD
```

## Step 3 — Read the template

Always read `.github/pull_request_template.md` first — sections evolve.
Use the latest version verbatim as the skeleton. If the file is missing,
stop and do not invent a body.

## Step 4 — Build the PR body

Fill the template top to bottom. Read [template-mapping.md](template-mapping.md)
for the portable section → source mapping and failure handling. Honor every row.

### Filling rules (strict)

1. Never leave template placeholders (`<…>`, `…`, "TBD", "TODO") in the final body.
2. Remove unused sections explicitly; do not leave empty checklists.
3. Preserve markdown structure unless a section is removed wholesale.
4. Do not summarize evidence the template asks to paste — paste verbatim.
5. Do not invent links — if no issue exists, leave the issue line empty.

## Step 5 — Open the PR

```bash
gh pr create \
  --base main \
  --head "$(git rev-parse --abbrev-ref HEAD)" \
  --title "<type>(<scope>): <description>" \
  --body "$(cat <<'EOF'
<the FULL filled template here>
EOF
)"
```

Prefer repository conventions for title and branch names when documented.
If the body is large, write it to a temp file and pass `--body-file`.

## Step 6 — Confirm and report

After successful creation, print the PR URL, title, base, and head.

## Step 7 — Publish pending review notes (if applicable)

If a review skill already produced a verdict that was waiting for a PR URL,
publish it now following that skill's publish instructions.
