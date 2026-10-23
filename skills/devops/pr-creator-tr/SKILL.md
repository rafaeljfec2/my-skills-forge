---
name: pr-creator-tr
description: >-
  Creates GitHub Pull Requests following TR team standards with Azure DevOps
  integration. Auto-links work items using AB# syntax, fills the PR template
  with description, changes, test evidence, and reviewer notes. Use when the
  user asks to create a PR for TR workflows. Do not use for portable
  template-only PRs (gh-create-pr) or Outcoders/Axiom Chat (pr-creator-outcoders).
---

# PR Creator — TR / Azure DevOps

Team-coupled PR opener for TR + Azure DevOps + Teams via `gh` and local config.

## When not to use

- Portable PR from any repo template → `gh-create-pr`
- Outcoders / Axiom Chat tool flow → `pr-creator-outcoders`

## When to use

- Create / open a PR
- Submit changes for review
- Push and create a pull request

## Prerequisites

Steps 8 and 9 (ADO update + Teams notification) require
`~/.cursor/pr-automation-config.json`. If missing, skip steps 8–9 and warn
(see [references/evidence-and-config.md](references/evidence-and-config.md)).

## Workflow (thin orchestrator)

1. Steps 1–9 (gather → validate → template → title/body → create → evidence → ADO → Teams) → [references/workflow-steps.md](references/workflow-steps.md)
2. Evidence images + config setup → [references/evidence-and-config.md](references/evidence-and-config.md)
3. ADO work item update → [references/azure-devops-update.md](references/azure-devops-update.md)
4. Teams Adaptive Card → [references/teams-notification.md](references/teams-notification.md)

## Token economy

Keep the injectable surface small. Read the reference the current step needs;
do not paste entire reference files into the reply.
