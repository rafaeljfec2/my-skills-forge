# Azure DevOps Work Item Update

Used by `pr-creator-ado` SKILL Step 8.

## Prerequisites

Read `~/.cursor/pr-automation-config.json`. If missing, skip Steps 8 and 9 and warn the user.

## Behavior

Read the current value of the configured ADO field, then append the PR link only if it is not already there. Avoids duplicates on retries.

## Script

```bash
CONFIG_FILE="$HOME/.cursor/pr-automation-config.json"
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

Replace `<US_NUMBER>` (work item ID extracted from branch name) and `<PR_URL>` (URL returned by `gh pr create`).

## Result handling

| Outcome | Message to user |
|---|---|
| Link already present | "PR link already present in US AB#<US_NUMBER>, skipping." |
| HTTP 200 | "US AB#<US_NUMBER> updated with PR link." |
| Other HTTP code | Warn user but continue to Step 9. |
