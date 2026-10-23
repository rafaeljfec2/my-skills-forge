---
name: context-budget-guard
description: >-
  Audit every markdown file consumed by Cursor/Claude Code agents
  (`.cursor/rules/*.mdc`, `.cursor/skills/**/*.md`, `.claude/skills/**/*.md`,
  `AGENTS.md`, `CLAUDE.md`, `.github/pull_request_template.md`) and verify each
  one fits within its category token budget. Use when auditing context budget,
  checking rule/skill sizes, or before publishing changes to rules/skills.
  Do NOT use to optimize production source code or to estimate API/LLM cost.
metadata:
  version: '1.0.0'
  short-description: Enforce token-budget limits on agent-consumed markdown files
---

# Cursor Context Budget Guard

Audits agent-consumed markdown and fails fast when a budget is exceeded.

## When not to use

- Production source refactoring / code size → use project refactoring guidance
- LLM API cost estimation → out of scope

## Why this exists

Cursor injects rules, skills, and root agent docs into prompts. Oversized files
slow the agent, hurt recall, get truncated, and raise cost. This skill measures
and enforces per-category budgets (`tokens ≈ bytes / 3.5`).

## Workflow (thin orchestrator)

1. Budget table and conversion rule → [references/budgets.md](references/budgets.md)
2. Run audit, interpret report, remediate, optional CI → [references/audit-workflow.md](references/audit-workflow.md)

Quick start (forge or harness install path):

```bash
python3 skills/ai-agents/context-budget-guard/scripts/audit_budget.py --root .
# or: python3 <skill-dir>/scripts/audit_budget.py --root <repo>
```

## Token economy

Keep the injectable surface small. Read the reference the current step needs;
do not paste entire reference files into the reply.
