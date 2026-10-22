# Senior Code Reviewer — Publishing the Review to a PR

When the review was requested for a specific PR (URL passed by the user, `owner/repo#number`, or remote review mode), the verdict from STEP 7 MUST be published as a comment on that PR.

Local reviews of uncommitted changes do NOT post anywhere — return in chat only.

## When to publish

Publish if ANY of the following is true:

- User provided a GitHub PR URL (e.g., `https://github.com/owner/repo/pull/123`)
- User specified `owner/repo#number` or `pr_number` parameters
- Review mode is REMOTE (always implies a target PR)
- Review was triggered as part of a PR-creation workflow that has just opened the PR

Do NOT publish if:

- Reviewing uncommitted local changes (no PR exists yet)
- Reviewing a branch not yet pushed to remote
- User explicitly asked for chat-only review

## Tooling — local mode (`gh` CLI)

```bash
gh pr comment <pr-number> --repo <owner>/<repo> --body "$(cat <<'EOF'
## Senior Code Review (AI-generated)

<entire STEP 7 verdict block — verbatim, no truncation>

---
_Automated review by `senior-code-reviewer` skill. Verify CRITICAL/IMPORTANT items before merging._
EOF
)"
```

## Tooling — remote mode (MCP)

If `gh` is unavailable, use the equivalent MCP tool (e.g., `git_pr_review_comment`, `git_pr_comment`) with the same body content. Same comment formatting requirements apply.

## Optional — submit a formal PR review (status badge)

Default behavior is a plain comment via `gh pr comment`. Use a formal GitHub review (`gh pr review`) only when explicitly requested or when branch protection requires it.

```bash
# REJECTED → request changes
gh pr review <pr-number> --repo <owner>/<repo> --request-changes --body "<one-line summary>"

# APPROVED_WITH_NOTES → comment review
gh pr review <pr-number> --repo <owner>/<repo> --comment --body "<one-line summary>"

# APPROVED → approve review (only if the reviewer identity is authorized)
gh pr review <pr-number> --repo <owner>/<repo> --approve --body "<one-line summary>"
```

## Comment formatting requirements

1. Header line MUST identify the review as AI-generated: `## Senior Code Review (AI-generated)`
2. Include the FULL verdict block from STEP 7 — no truncation, no summarization, no paraphrasing
3. Use markdown so GitHub renders sections, code blocks, and lists correctly
4. Keep `file:line` references as plain text — GitHub auto-linkifies when the path matches a file in the repo
5. Add a footer attributing the review to the `senior-code-reviewer` skill

## Confirmation

After successful publish, print to chat:

```
PUBLISHED: <PR URL>#issuecomment-<id>
```

If publishing fails (auth error, missing repo access, network), do NOT silently swallow the error:

1. Print the exact failure message
2. Emit the full review verdict in chat as fallback
3. Never report the review as "delivered" when it was not actually posted
