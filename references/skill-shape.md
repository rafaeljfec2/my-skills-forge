# Skill shape (thin orchestrator)

Canonical shape for every catalog skill under `skills/<domain>/<name>/`.
Inspired by Akita-style token economy; content remains forge-owned.

## Required `SKILL.md` sections

```text
---
name: <kebab-case matching folder>
description: >-
  When to use. Include Do NOT use neighbors when a sibling skill overlaps.
---

# <Title>

<Role — short>

## When not to use          # required when a catalog sibling overlaps

## <skill-specific MUST / persona — keep short>

## Workflow (thin orchestrator)   # REQUIRED
## Token economy                  # REQUIRED
```

## Rules

1. Prefer `SKILL.md` ≤ 1,500 tokens (`tokens ≈ bytes / 3.5`). Must stay under soft 2,500 / hard 4,000.
2. Put phases, checklists, stack detail, and templates in `references/*.md` (soft 5,000 / hard 7,000).
3. Workflow is an **index**: numbered steps that link to the reference needed for that step.
4. Token economy: read only the reference the current step needs; do not paste whole refs into the reply.
5. Skills under ~1,000 tokens may keep content inline but must still include the two required headings.
6. Scripts live under `scripts/` and are not injected as prompt text.

## Reference pattern

```text
skills/<domain>/<name>/
  SKILL.md
  references/
    <step-or-topic>.md
  scripts/          # optional
```

## Validation

`_validate.py` requires the headings `## Workflow (thin orchestrator)` and
`## Token economy` on every catalog `SKILL.md`. Budget is measured with
`skills/ai-agents/context-budget-guard/scripts/audit_budget.py --root .`.
