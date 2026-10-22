# PR Creator — Claude Code Setup

Slash command for Claude Code that creates GitHub Pull Requests with Azure DevOps integration and Microsoft Teams notifications.

## Features

- Auto-extracts US number from branch name (`feat/AB#<NUMBER>-...`)
- Validates mandatory fields before creating (US number + test evidence images)
- Fills the repo's PR template automatically
- Uploads test evidence images via draft release workaround
- Updates Azure DevOps Work Item with PR link (with duplicate detection)
- Sends Adaptive Card notification to Teams channel with reviewer @mentions

## Installation

### 1. Copy the slash command

Copy `create-pr.md` into your project's `.claude/commands/` directory:

```bash
mkdir -p .claude/commands
cp create-pr.md .claude/commands/create-pr.md
```

> To make it available across all projects, place it in `~/.claude/commands/` instead.

### 2. Create the config file

Create `~/.claude/pr-automation-config.json`:

```json
{
  "azureDevOps": {
    "organization": "your-org",
    "project": "Your Project",
    "pat": "<PERSONAL_ACCESS_TOKEN>",
    "prLinkField": "Custom.DescriptionofRootCause"
  },
  "teams": {
    "webhookUrl": "<TEAMS_INCOMING_WEBHOOK_URL>"
  },
  "reviewers": [
    { "name": "John Doe", "email": "john.doe@company.com" },
    { "name": "Jane Smith", "email": "jane.smith@company.com" }
  ]
}
```

### 3. Configure each field

#### Azure DevOps PAT

1. Go to `https://dev.azure.com/<your-org>/_usersSettings/tokens`
2. Click **"New Token"**
3. Set scope: **Work Items → Read & Write**
4. Copy the token into `pat`

#### Teams Webhook URL

1. In the target Teams channel, click `...` → **Workflows**
2. Select **"Post to a channel when a webhook request is received"**
3. Choose the channel and copy the generated URL into `webhookUrl`

#### Reviewers

Add each reviewer with their display name and corporate email. The email must match their Microsoft Teams / Entra ID account for @mentions to work.

### 4. Validate config

```bash
python3 -c "import json; json.load(open('$HOME/.claude/pr-automation-config.json')); print('Config OK')"
```

## Usage

In Claude Code, run:

```
/create-pr
```

Or simply ask Claude Code to create a PR — it will follow the command instructions.

## Requirements

- `gh` CLI authenticated (`gh auth login`)
- `git` configured with remote access
- `python3` available in PATH
- `curl` available in PATH
