---
name: pr-creator-tr
description: Creates GitHub Pull Requests following TR team standards with Azure DevOps integration. Auto-links work items using AB# syntax, fills the PR template with description, changes, test evidence, and reviewer notes. Use when the user asks to create a PR, open a pull request, or submit changes for review.
---

# PR Creator — TR / Azure DevOps

## When to Use

Activate this skill when the user asks to:

- Create / open a PR
- Submit changes for review
- Push and create a pull request

## Prerequisites

Steps 8 and 9 (ADO update + Teams notification) require a config file at `~/.cursor/pr-automation-config.json`. If it does not exist, **skip steps 8 and 9** and warn the user:

> "Config file `~/.cursor/pr-automation-config.json` not found. Skipping ADO work item update and Teams notification. See `references/evidence-and-config.md`."

Read the config file once at the beginning of step 8 and reuse the parsed values for both steps.

## Workflow

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

- `AB#1060986 Adicionar campos TECNOS (Exigibilidade ISS e Código de Serviço Nacional)`
- `AB#1056408 Implementar termos de uso do Domínio Rewards`

The `AB#<number>` prefix auto-links to Azure DevOps work items.

### 5. Fill the PR Body

Use the repository's template sections. Map content as follows:

| Template Section            | Content                                                                                                                                                                                       |
| --------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Descrição**               | First line: `**US**: [AB#<NUMBER>](<ADO_URL>)` with the link. Then 1-2 sentences about what was done and why. Use `azure_devops_work_item` MCP tool to get URL from `_links.html.href`        |
| **O que a PR faz**          | Bullet list of changes grouped by feature/area                                                                                                                                                |
| **Evidências de Teste**     | **Mandatory.** Screenshots from step 2. Upload via draft release workaround (see `references/evidence-and-config.md`) and embed as markdown images                                            |
| **Observações ao revisor**  | Technical notes: dependencies, env config, breaking changes, data flow nuances                                                                                                                |
| **Code Review Checklist**   | Mark items as `[x]` for applicable, `[ ]` with `(N/A)` for non-applicable                                                                                                                     |

For PRs touching 5+ files, add a summary table:

```markdown
| Arquivo             | Descrição                  |
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

## Conventions

Branch naming, checklist conventions, evidence image upload, and the full config setup live in `references/evidence-and-config.md`.
