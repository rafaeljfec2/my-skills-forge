# PR Creator — Azure DevOps + GitHub + Teams

## Trigger

Run this command when the user asks to create a PR, open a pull request, or submit changes for review.

## Prerequisites

Steps 8 and 9 (ADO update + Teams notification) require a config file at `~/.claude/pr-automation-config.json`.

If the file does not exist, **skip steps 8 and 9** and warn the user:
> "Config file `~/.claude/pr-automation-config.json` not found. Skipping ADO work item update and Teams notification. Run `/create-pr-setup` to configure."

Read the config file once at the beginning of step 8 and reuse the parsed values for both steps.

## Workflow

### 1. Gather Context

Run these commands:

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

Before proceeding, you **MUST** have both items below. If any is missing, **STOP and ask the user**. Do NOT continue to step 3 without them.

#### 2.1 US Number (mandatory)

Try to extract from the branch name (pattern `AB#<NUMBER>`). If the branch does not follow the naming convention:
> "Could not extract the US number from the branch name `<branch>`. Please provide the Azure DevOps User Story number (e.g. `1060986`)."

#### 2.2 Test Evidence Images (mandatory)

Check if the user provided screenshots or image paths in their request. If no images were provided:
> "Test evidence images are required to create the PR. Please provide file paths to screenshots showing the tested scenarios."

**Only proceed to step 3 after both the US number and at least one test evidence image path are confirmed.**

### 3. Identify the PR Template

Read the repository's PR template:

```bash
cat .github/pull_request_template.md
```

The template defines the sections to fill. Always respect the repository's template structure.

### 4. Build the PR Title

Format: `AB#<US_NUMBER> <concise description of what was done>`

Examples:
- `AB#1060986 Adicionar campos TECNOS (Exigibilidade ISS e Código de Serviço Nacional)`
- `AB#1056408 Implementar termos de uso do Domínio Rewards`

The `AB#<number>` prefix auto-links to Azure DevOps work items.

### 5. Fill the PR Body

Use the repository's template sections. Map content as follows:

| Template Section | Content |
|---|---|
| **Descrição** | First line: `**US**: [AB#<NUMBER>](<ADO_URL>)` with the link to the work item. Then 1-2 sentences about what was done and why. Construct the URL as `https://dev.azure.com/<ORG>/<PROJECT>/_workitems/edit/<US_NUMBER>` |
| **O que a PR faz** | Bullet list of all changes grouped by feature/area |
| **Evidências de Teste** | **Mandatory.** Screenshots provided by the user in step 2. Upload via draft release workaround and embed as markdown images |
| **Observações ao revisor** | Technical notes: dependencies, env config, breaking changes, data flow nuances |
| **Code Review Checklist** | Mark items as `[x]` for applicable, `[ ]` with `(N/A)` for non-applicable |

#### Changes Table (optional, for PRs with many files)

When the PR touches 5+ files, add a summary table:

```markdown
| Arquivo | Descrição |
|---------|-----------|
| `ComponentName.tsx` | Brief description of change |
| `hookName.ts` | Brief description of change |
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
- Upload test evidence images using the draft release workaround (see "Evidence Images" section below) and update the PR body with the image URLs

### 8. Update Azure DevOps Work Item

Read `~/.claude/pr-automation-config.json`. If it does not exist, warn the user and skip steps 8 and 9.

First read the current field value to avoid duplicates, then append the PR link only if it is not already present:

```bash
CONFIG_FILE="$HOME/.claude/pr-automation-config.json"
ADO_PAT=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE'))['azureDevOps']['pat'])")
ADO_ORG=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE'))['azureDevOps']['organization'])")
ADO_PROJECT=$(python3 -c "import json; d=json.load(open('$CONFIG_FILE')); print(d['azureDevOps']['project'].replace(' ', '%20'))")
ADO_FIELD=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE'))['azureDevOps']['prLinkField'])")
AUTH=$(echo -n ":${ADO_PAT}" | base64 -w 0)

CURRENT_VALUE=$(curl -s --http1.1 \
  "https://dev.azure.com/${ADO_ORG}/${ADO_PROJECT}/_apis/wit/workitems/<US_NUMBER>?fields=${ADO_FIELD}&api-version=7.1" \
  -H "Authorization: Basic ${AUTH}" \
  | python3 -c "import json,sys; print(json.load(sys.stdin).get('fields',{}).get('${ADO_FIELD}',''))" 2>/dev/null)

if echo "$CURRENT_VALUE" | grep -q "<PR_URL>"; then
  echo "PR link already exists in field. Skipping update."
else
  NEW_VALUE="${CURRENT_VALUE}<div><a href=\"<PR_URL>\"><PR_URL></a></div>"
  HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" --http1.1 -X PATCH \
    "https://dev.azure.com/${ADO_ORG}/${ADO_PROJECT}/_apis/wit/workitems/<US_NUMBER>?api-version=7.1" \
    -H "Content-Type: application/json-patch+json" \
    -H "Authorization: Basic ${AUTH}" \
    -d "[{\"op\":\"replace\",\"path\":\"/fields/${ADO_FIELD}\",\"value\":\"$(echo "$NEW_VALUE" | python3 -c "import sys,json; print(json.dumps(sys.stdin.read().strip())[1:-1])")\"}]")
fi
```

Replace `<US_NUMBER>` with the work item ID extracted from the branch name (step 1) and `<PR_URL>` with the GitHub PR URL returned by `gh pr create` (step 6).

- **PR link already exists**: skip the update and inform the user: "PR link already present in US AB#<US_NUMBER>, skipping."
- **HTTP 200** = success. Inform the user: "US AB#<US_NUMBER> updated with PR link."
- **Any other status** = warn the user but do NOT block the flow. Continue to step 9.

### 9. Notify Teams Channel

Read reviewers and webhook URL from the same config file parsed in step 8.

Build a temporary JSON file with the Adaptive Card payload:

```bash
WEBHOOK_URL=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE'))['teams']['webhookUrl'])")

python3 -c "
import json

config = json.load(open('$HOME/.claude/pr-automation-config.json'))
reviewers = config['reviewers']

mentions_text = ', '.join(f'<at>{r[\"name\"]}</at>' for r in reviewers)
entities = [
    {
        'type': 'mention',
        'text': f'<at>{r[\"name\"]}</at>',
        'mentioned': {'id': r['email'], 'name': r['name']}
    }
    for r in reviewers
]

card = {
    'type': 'message',
    'attachments': [{
        'contentType': 'application/vnd.microsoft.card.adaptive',
        'content': {
            'type': 'AdaptiveCard',
            '\$schema': 'http://adaptivecards.io/schemas/adaptive-card.json',
            'version': '1.4',
            'body': [
                {
                    'type': 'Container',
                    'style': 'accent',
                    'bleed': True,
                    'items': [{
                        'type': 'TextBlock',
                        'text': '\U0001F500 New Pull Request',
                        'weight': 'Bolder',
                        'size': 'Medium',
                        'color': 'Light'
                    }],
                    'padding': {'top': 'Default', 'bottom': 'Default', 'left': 'Default', 'right': 'Default'}
                },
                {
                    'type': 'TextBlock',
                    'text': '<PR_TITLE>',
                    'weight': 'Bolder',
                    'size': 'Medium',
                    'wrap': True,
                    'spacing': 'Medium'
                },
                {
                    'type': 'ColumnSet',
                    'spacing': 'Medium',
                    'columns': [
                        {
                            'type': 'Column',
                            'width': 'auto',
                            'items': [
                                {'type': 'TextBlock', 'text': '\U0001F4CB User Story', 'size': 'Small', 'isSubtle': True, 'spacing': 'None'},
                                {'type': 'TextBlock', 'text': '[AB#<US_NUMBER>](<ADO_URL>)', 'weight': 'Bolder', 'spacing': 'Small'}
                            ]
                        },
                        {
                            'type': 'Column',
                            'width': 'auto',
                            'separator': True,
                            'spacing': 'Large',
                            'items': [
                                {'type': 'TextBlock', 'text': '\U0001F517 Pull Request', 'size': 'Small', 'isSubtle': True, 'spacing': 'None'},
                                {'type': 'TextBlock', 'text': '[#<PR_NUMBER>](<PR_URL>)', 'weight': 'Bolder', 'spacing': 'Small'}
                            ]
                        }
                    ]
                },
                {
                    'type': 'Container',
                    'spacing': 'Medium',
                    'separator': True,
                    'items': [
                        {'type': 'TextBlock', 'text': '\U0001F465 Reviewers', 'size': 'Small', 'isSubtle': True, 'spacing': 'None'},
                        {'type': 'TextBlock', 'text': mentions_text, 'wrap': True, 'spacing': 'Small'}
                    ]
                },
                {
                    'type': 'ActionSet',
                    'spacing': 'Medium',
                    'actions': [
                        {'type': 'Action.OpenUrl', 'title': '\U0001F50D Open PR', 'url': '<PR_URL>', 'style': 'positive'},
                        {'type': 'Action.OpenUrl', 'title': '\U0001F4DD Open US', 'url': '<ADO_URL>'}
                    ]
                }
            ],
            'msteams': {'entities': entities}
        }
    }]
}

with open('/tmp/pr-teams-notification.json', 'w') as f:
    json.dump(card, f)
"
```

Replace the placeholders before running:
- `<PR_TITLE>`: the PR title from step 4
- `<US_NUMBER>`: the work item ID from step 1
- `<ADO_URL>`: the ADO work item URL (constructed as `https://dev.azure.com/<ORG>/<PROJECT>/_workitems/edit/<US_NUMBER>`)
- `<PR_NUMBER>`: the PR number returned by `gh pr create` (step 6)
- `<PR_URL>`: the full GitHub PR URL

Send the notification:

```bash
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
  -H "Content-Type: application/json" \
  -d @/tmp/pr-teams-notification.json \
  "${WEBHOOK_URL}")

rm -f /tmp/pr-teams-notification.json
```

- **HTTP 200 or 202** = success. Inform the user: "Teams notification sent to the channel."
- **Any other status** = warn the user but do NOT block the flow.

## Evidence Images

GitHub has **no public API** for uploading images to PR bodies. Use the **draft release workaround**:

```bash
gh release create pr-<NUMBER>-evidence \
  --title "PR #<NUMBER> - Evidence Images" \
  --notes "Temporary release for PR evidence images." \
  --draft \
  "/path/to/image1.png" \
  "/path/to/image2.png"

gh release view pr-<NUMBER>-evidence --json assets -q '.assets[] | "\(.name) \(.url)"'
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
