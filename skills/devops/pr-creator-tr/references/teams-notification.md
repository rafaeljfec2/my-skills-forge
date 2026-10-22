# Teams Channel Notification

Used by `pr-creator-ado` SKILL Step 9.

Reads webhook URL and reviewers from `~/.cursor/pr-automation-config.json`.

## Build the Adaptive Card payload

```bash
WEBHOOK_URL=$(python3 -c "import json; print(json.load(open('$HOME/.cursor/pr-automation-config.json'))['teams']['webhookUrl'])")

python3 -c "
import json

config = json.load(open('$HOME/.cursor/pr-automation-config.json'))
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

## Placeholders

Replace before running:

- `<PR_TITLE>` — PR title from Step 4
- `<US_NUMBER>` — work item ID from Step 1
- `<ADO_URL>` — `_links.html.href` via MCP, or `https://dev.azure.com/tr-ggo/TR%20Fintech/_workitems/edit/<US_NUMBER>`
- `<PR_NUMBER>` — PR number from `gh pr create`
- `<PR_URL>` — full GitHub PR URL

## Send

```bash
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
  -H "Content-Type: application/json" \
  -d @/tmp/pr-teams-notification.json \
  "${WEBHOOK_URL}")

rm -f /tmp/pr-teams-notification.json
```

## Result handling

| HTTP Status | Action |
|---|---|
| 200 / 202 | "Teams notification sent to the channel." |
| Other | Warn user; do NOT block flow. |
