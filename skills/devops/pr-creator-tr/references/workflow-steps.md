# PR creation workflow

### 1. Gather Context

Run these commands **in parallel**:

```bash
git status
git log --oneline develop..HEAD
git diff develop..HEAD --stat
git branch --show-current
git remote -v | head -2
gh pr list --head "$(git branch --show-current)" --state all
```

Extract:

- **Branch name**: must follow `feat/AB#<US_NUMBER>-<short-description>`
- **US number**: from the branch name (e.g. `AB#1060986`)
- **Commits**: all commits ahead of `develop`
- **Changed files**: summary with file count and lines changed
- **Remote**: confirm branch is pushed; if not, run `git push -u origin HEAD`

### 2. Validate Required Information

You **MUST** have both items below. If any is missing, **STOP and ask the user**.

#### 2.1 US Number (mandatory)

Try to extract from branch name (`AB#<NUMBER>` pattern). If absent:

> "Could not extract the US number from the branch name `<branch>`. Please provide the Azure DevOps User Story number (e.g. `1060986`)."

#### 2.2 Test Evidence Images (mandatory)

Check if the user provided screenshots or image paths. If none:

> "Test evidence images are required to create the PR. Please provide screenshots showing the tested scenarios (paste images in the chat or provide file paths)."

**Only proceed to step 3 after both the US number and at least one test evidence image are confirmed.**

### 3. Identify the PR Template

```bash
cat .github/pull_request_template.md
```

Always respect the repository's template structure.

### 4. Build the PR Title

Format: `AB#<US_NUMBER> <concise description of what was done>`

Examples:

- `AB#1060986 Add TECNOS fields (ISS taxability and national service code)`
- `AB#1056408 Implement Rewards domain terms of use`

The `AB#<number>` prefix auto-links to Azure DevOps work items.

### 5. Fill the PR Body

Use the repository's template sections. Map content as follows:

| Template Section            | Content                                                                                                                                                                                       |
| --------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Description**             | First line: `**US**: [AB#<NUMBER>](<ADO_URL>)` with the link. Then 1-2 sentences about what was done and why. Use `azure_devops_work_item` MCP tool to get URL from `_links.html.href`        |
| **What this PR does**       | Bullet list of changes grouped by feature/area                                                                                                                                                |
| **Test evidence**           | **Mandatory.** Screenshots from step 2. Upload via draft release workaround (see `references/evidence-and-config.md`) and embed as markdown images                                            |
| **Notes for the reviewer**  | Technical notes: dependencies, env config, breaking changes, data flow nuances                                                                                                                |
| **Code Review Checklist**   | Mark items as `[x]` for applicable, `[ ]` with `(N/A)` for non-applicable                                                                                                                     |

For PRs touching 5+ files, add a summary table:

```markdown
| File                | Description                |
| ------------------- | -------------------------- |
| `ComponentName.tsx` | Brief description of change |
| `hookName.ts`       | Brief description of change |
```

### 6. Create the PR

```bash
gh pr create \
  --base develop \
  --head "<branch-name>" \
  --title "AB#<US_NUMBER> <description>" \
  --body "$(cat <<'EOF'
<filled template content>
EOF
)"
```

**Important**: Always use `--base develop` unless the user specifies otherwise.

### 7. Post-Creation

- Return the PR URL to the user
- Upload test evidence images (see `references/evidence-and-config.md` § "Evidence Images") and update the PR body with the image URLs

### 8. Update Azure DevOps Work Item

Follow `references/azure-devops-update.md`. Reads `~/.cursor/pr-automation-config.json`, fetches the current field value, and appends the PR link only if not already present.

### 9. Notify Teams Channel

Follow `references/teams-notification.md`. Builds an Adaptive Card with US/PR/reviewers and posts via webhook. Reuse the parsed config from step 8.

