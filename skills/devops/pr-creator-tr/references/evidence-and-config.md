# Evidence Images + Config Setup

## Evidence Images (draft release workaround)

GitHub has **no public API** for uploading images to PR bodies. Use the draft release pattern:

```bash
# 1. Create a draft release with images as assets
gh release create pr-<NUMBER>-evidence \
  --title "PR #<NUMBER> - Evidence Images" \
  --notes "Temporary release for PR evidence images." \
  --draft \
  "/path/to/image1.png" \
  "/path/to/image2.png"

# 2. Get the asset download URLs
gh release view pr-<NUMBER>-evidence --json assets -q '.assets[] | "\(.name) \(.url)"'

# 3. Use the URLs in the PR body as standard markdown images
# ![Description](https://github.com/org/repo/releases/download/tag/filename.png)
```

After the PR is merged, the draft release can be deleted:

```bash
gh release delete pr-<NUMBER>-evidence --yes
```

## Checklist Conventions

For the Code Review Checklist:

- `[x]` = validated and confirmed
- `[ ]` with `(N/A)` = not applicable to this PR
- `[ ]` = not yet validated (avoid leaving these unless intentional)

## Branch Naming

If the user hasn't created a branch yet, suggest:

```
feat/AB#<US_NUMBER>-<short-kebab-description>
```

Examples:

- `feat/AB#1060986-add-tecnos-fields`
- `fix/AB#1055432-fix-invoice-validation`
- `chore/AB#1070001-update-dependencies`

## PR Automation Config (`~/.cursor/pr-automation-config.json`)

Steps 8 and 9 require this file. It lives outside the repository to avoid leaking secrets.

### Structure

```json
{
  "azureDevOps": {
    "organization": "tr-ggo",
    "project": "TR Fintech",
    "pat": "<PERSONAL_ACCESS_TOKEN>",
    "prLinkField": "Custom.DescriptionofRootCause"
  },
  "teams": {
    "webhookUrl": "<POWER_AUTOMATE_WEBHOOK_URL>"
  },
  "reviewers": [{ "name": "Display Name", "email": "user@thomsonreuters.com" }]
}
```

### Setup

1. **Azure DevOps PAT**: Azure DevOps → User Settings → Personal Access Tokens. Create a token with scope **Work Items: Read & Write**. Copy into `pat`.
2. **Teams Webhook URL**: In the target Teams channel, click `...` → **Workflows** → **"Post to a channel when a webhook request is received"**. Select the channel and copy the generated URL into `webhookUrl`.
3. **Reviewers**: Add each reviewer with display name and corporate email. The email must match Microsoft Teams / Entra ID for @mentions to deliver.

### Validation

```bash
python3 -c "import json; json.load(open('$HOME/.cursor/pr-automation-config.json')); print('Config OK')"
```
