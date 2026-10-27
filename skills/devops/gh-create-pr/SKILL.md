---
name: gh-create-pr
description: >-
  Open a GitHub Pull Request for the current branch using `gh` and the
  repository's `.github/pull_request_template.md`, filling every applicable
  section from the current session context. Use when the user asks to open
  or create a PR. Do not use for amending an existing PR, addressing review
  comments, or fixing CI.
metadata:
  version: '1.2.0'
  short-description: Create a PR filling the project template from session context
---

# Create PR (template-driven)

## When not to use

- TR team ADO/Teams flow → `pr-creator-tr`
- Outcoders / Axiom Chat flow → `pr-creator-outcoders`
- Amend existing PR / address review comments / fix CI → other skills or session work

## Role

Open a Pull Request via `gh pr create` whose body is
`.github/pull_request_template.md` filled from the current session. The
template is the source of truth — never invent a body, leave placeholders, or
bypass the template. Portable: no hard-coded product gate IDs; follow the
current repository's documented gates (`AGENTS.md`, rules, template).

## Workflow (thin orchestrator)

1. Prerequisites, push, template read, body fill, `gh pr create`, confirm →
   [references/prerequisites-and-create.md](references/prerequisites-and-create.md)
2. Section → source mapping and failure handling →
   [references/template-mapping.md](references/template-mapping.md)

## Token economy

Keep the injectable surface small. Load the reference for the current step
only; do not paste entire references into the reply.
