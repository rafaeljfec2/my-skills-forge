---
name: reflect
description: >-
  Review recent work, find repeated workflow friction, and recommend the
  smallest useful reusable form (skill, command, prompt rule, playbook) or
  recommend creating nothing. Use when the user asks to reflect, learn from
  sessions, curb skill sprawl, or decide whether a recurring process should
  become an agent asset. Do not use for ordinary implementation, one-off
  debugging, PR review, or speculative skill creation without workflow evidence.
---

# Reflect

Orchestrator-only curation workflow. Look back over recent sessions and
existing forge/harness assets, then recommend the smallest useful improvement —
or explicitly recommend creating nothing when evidence is weak.

## When not to use

- Implementing features or fixing bugs → project engineering skills
- PR / code review verdicts → `senior-code-review-judge` / `senior-code-reviewer-protocol`
- Author delivery closeout → `principal-engineering-workflow`
- Inventing skills without repeated friction evidence → stop; this skill forbids that

## Core contract

- Inspect existing assets before suggesting new ones
- Prefer recent, repeated, user-visible friction over isolated incidents
- Recommend the smallest useful form
- Treat **create nothing** as a successful result when evidence is weak
- Ask before writing skills, prompts, commands, or config
- Avoid near-duplicates of forge catalog skills

## Workflow (thin orchestrator)

1. Score candidates and choose form → [references/scoring.md](references/scoring.md)
2. Emit the report → [references/output-template.md](references/output-template.md)

Evidence order: current conversation → project guidance → existing forge/harness
skills → recent session notes (when available and safe) → external docs only when
a proposal depends on a third-party tool.

## Token economy

Keep the injectable surface small. Read the reference the current step needs;
do not paste entire reference files into the reply.
