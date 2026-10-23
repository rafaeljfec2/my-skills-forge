---
name: pr-creator-outcoders
description: >-
  Creates GitHub Pull Requests following Outcoders team standards with Azure
  DevOps integration. Auto-links work items using AB# syntax, fills the PR
  template with description, changes, test evidence, and reviewer notes. Use
  when creating a PR for Outcoders / Axiom Chat workflows. Do not use for
  portable template-only PRs (gh-create-pr) or TR team standards (pr-creator-tr).
---

# PR Creator — Outcoders / Azure DevOps

Team-coupled PR opener for Outcoders + Azure DevOps + Teams via Axiom Chat tools.

## When not to use

- Portable PR from any repo template → `gh-create-pr`
- TR team standards / local gh + config file → `pr-creator-tr`

## When to use

- Create / open a PR
- Submit changes for review
- Push and create a pull request

## Workflow (thin orchestrator)

Execute steps in order. Load detail only when the step needs it:

1. Tool map → [references/tools.md](references/tools.md)
2. Steps 1–10 (gather → validate → ADO → template → title/body → create → ADO update → Teams → report) → [references/workflow-steps.md](references/workflow-steps.md)
3. Branch naming, checklist marks, evidence upload → [references/conventions-and-evidence.md](references/conventions-and-evidence.md)

## Token economy

Keep the injectable surface small. Read the reference the current step needs;
do not paste entire reference files into the reply.
