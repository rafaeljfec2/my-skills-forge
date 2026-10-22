---
name: pr-creator-outcoders
description: >-
  Creates GitHub Pull Requests following Outcoders team standards with Azure DevOps
  integration. Auto-links work items using AB# syntax, fills the PR template
  with description, changes, test evidence, and reviewer notes. Activates when
  the user asks to create a PR, open a pull request, or submit changes for review.
---

# PR Creator — Outcoders / Azure DevOps

## When to Use

Activate this skill when the user asks to:
- Create / open a PR
- Submit changes for review
- Push and create a pull request

## Available Tools

This skill uses the following Axiom Chat tools:

| Tool | Purpose |
|---|---|
| `git_list_branches` | List repository branches |
| `git_list_commits` | List commits on a branch |
| `git_list_prs` | Check if a PR already exists |
| `git_diff_stat` | Compare branches (changed files with additions/deletions) |
| `git_pr_create` | Create the pull request |
| `ado_work_item_detail` | Fetch ADO work item details (title, description, URL) |
| `ado_work_item_update` | Link the PR back to the ADO work item |
| `teams_notify` | Send PR notification to Teams channel with Adaptive Card |
| `workspace_read_file` | Read the PR template from `.github/pull_request_template.md` |

## Workflow

### 1. Gather Context

Call these tools to collect information:

1. **`git_list_branches`** — find the current feature branch
2. **`git_list_commits`** with `sha` set to the feature branch — get commits
3. **`git_list_prs`** — check if a PR already exists for this branch
4. **`git_diff_stat`** with `head` set to the feature branch and `base` set to `develop` — get changed files with line counts

Extract:
- **Branch name**: should follow `feat/AB#<US_NUMBER>-<short-description>`
- **US number**: from the branch name (e.g. `AB#1060986`)
- **Commits**: all commits ahead of `develop`
- **Changed files**: from `git_diff_stat` output

If a PR already exists for the branch, inform the user and ask if they want to update it.

### 2. Validate Required Information

Before proceeding, you **MUST** have both items below. If any is missing, **STOP and ask the user**.

#### 2.1 US Number (mandatory)

Try to extract from the branch name (pattern `AB#<NUMBER>`). If not found:
> "Could not extract the US number from the branch name `<branch>`. Please provide the Azure DevOps User Story number (e.g. `1060986`)."

#### 2.2 Test Evidence (mandatory)

Check if the user provided screenshots, image paths, or described tested scenarios. If not:
> "Test evidence is required to create the PR. Please provide screenshots or describe what was tested."

**Only proceed after both the US number and test evidence are confirmed.**

### 3. Fetch ADO Work Item Details

Call **`ado_work_item_detail`** with `work_item_id` set to the US number. Extract:
- Work item title
- Description (business context)
- Acceptance criteria
- Direct URL (from `_links.html.href` in the response)

### 4. Read PR Template

Call **`workspace_read_file`** with `relative_path` set to `.github/pull_request_template.md`. Use this template to structure the PR body.

### 5. Build the PR Title

Format: `AB#<US_NUMBER> <concise description of what was done>`

Examples:
- `AB#1060986 Add TECNOS fields (ISS exigibility and national service code)`
- `AB#1056408 Implement Domínio Rewards terms of use`

The `AB#<number>` prefix auto-links to Azure DevOps work items.

### 6. Fill the PR Body

Use the template sections from step 4. Map content as follows:

| Template Section | Content |
|---|---|
| **Description** | First line: `**US**: [AB#<NUMBER>](<ADO_URL>)`. Then 1-2 sentences about what was done and why |
| **What the PR does** | Bullet list of all changes from `git_diff_stat`, grouped by feature/area |
| **Test evidence** | Screenshots or descriptions provided by the user |
| **Reviewer notes** | Technical notes: dependencies, env config, breaking changes |
| **Code Review Checklist** | Mark `[x]` for applicable, `[ ] (N/A)` for non-applicable |

#### Changes Table (for PRs with many files)

When `git_diff_stat` shows 5+ changed files, add a summary table:

```markdown
| File | Description |
|---------|-----------|
| `ComponentName.tsx` | Brief description of change |
| `hookName.ts` | Brief description of change |
```

### 7. Create the PR

Call **`git_pr_create`** with:
- `title`: the title from step 5
- `body`: the filled template from step 6
- `head`: the feature branch name
- `base`: `develop` (unless the user specifies otherwise)
- `draft`: `false` (unless the user asks for a draft)

The tool returns the PR number and URL.

### 8. Update Azure DevOps Work Item

After the PR is created, call **`ado_work_item_update`** to link the PR back:

- `work_item_id`: the US number
- `fields`: `{"Custom.DescriptionofRootCause": "<existing_value><div><a href=\"<PR_URL>\">PR #<NUMBER> - <PR_TITLE></a></div>"}`

First read the current field value via `ado_work_item_detail` to avoid duplicating links.

If the update fails, warn the user but do NOT block the flow.

### 9. Notify Teams Channel

Call **`teams_notify`** with:
- `pr_title`: the PR title from step 5
- `pr_url`: the PR URL from step 7
- `pr_number`: the PR number from step 7
- `us_number`: the work item ID from step 2
- `ado_url`: the ADO URL from step 3

The tool automatically:
- Builds an Adaptive Card with PR info, US link, and action buttons
- Mentions configured reviewers (from `TEAMS_PR_REVIEWERS` tenant secret)
- Sends to the Teams webhook (`TEAMS_WEBHOOK_URL` tenant secret)

If Teams is not configured, the tool will inform the user — do NOT block the PR creation flow.

### 10. Report to User

Return a summary:
- PR URL and number
- ADO work item link status
- Teams notification status
- Reminder to request reviewers if needed

## Branch Naming Convention

| Prefix | When to use |
|--------|-------------|
| `feat/` | New feature or enhancement |
| `fix/` | Bug fix |
| `chore/` | Dependencies, config, CI changes |

Pattern: `<prefix>AB#<US_NUMBER>-<short-kebab-description>`

Examples:
- `feat/AB#1060986-add-tecnos-fields`
- `fix/AB#1055432-fix-invoice-validation`
- `chore/AB#1070001-update-dependencies`

## Checklist Conventions

For the Code Review Checklist:
- `[x]` = validated and confirmed
- `[ ]` with `(N/A)` = not applicable to this PR
- `[ ]` = not yet validated

## Evidence Images

If the user needs to upload images to the PR body and they aren't embeddable directly, suggest the draft release workaround:

```bash
gh release create pr-<NUMBER>-evidence \
  --title "PR #<NUMBER> - Evidence Images" \
  --notes "Temporary release for PR evidence images." \
  --draft \
  "/path/to/image.png"

gh release view pr-<NUMBER>-evidence --json assets -q '.assets[] | "\(.name) \(.url)"'
```

After the PR is merged:
```bash
gh release delete pr-<NUMBER>-evidence --yes
```
