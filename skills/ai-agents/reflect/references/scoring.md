# Reflect scoring

## Inventory existing assets first

Before proposing anything, identify what already exists:

- Forge catalog skills under `skills/<domain>/<name>/`
- Harness leftovers and vendor skills (see forge `references/external-inventory.md`)
- Project `AGENTS.md` / rules / playbooks
- Custom agents, commands, MCP permissions when relevant

If an existing asset already covers the candidate, recommend extending or using
it instead of creating a near-duplicate.

## Find repeated workflow patterns

Strong signals:

- The same command sequence across sessions
- The user repeatedly asks for the same review, setup, release, or debug process
- The same research or context-gathering steps keep recurring
- The same specialist routing decision is repeatedly needed
- The same project-specific rule is repeatedly re-explained
- Repeated failures because an agent lacks a stable instruction or tool boundary

Strong candidates usually have at least two occurrences, stable inputs, a clear
output, and a clear stopping condition.

## Score each candidate

| Dimension | Question |
|---|---|
| Frequency | How often has it happened? |
| Cost | Does it waste meaningful time, context, money, or attention? |
| Risk | Does inconsistent execution cause bugs, bad decisions, or unsafe changes? |
| Stability | Are inputs and desired output predictable? |
| Coverage | Is there already an asset that handles it well? |

Only recommend creating or changing assets when confidence is high.

## Choose the smallest useful form

Least powerful form that solves the repeated problem:

1. Prompt/config rule on an existing agent
2. Extend an existing forge skill
3. New skill (thin orchestrator + `references/`)
4. Command / manual trigger with stable inputs
5. Custom agent / specialist lane
6. MCP/tool permission change
7. Project playbook/doc (when automation is too heavy)
8. **Skip** — weak, one-off, ambiguous, sensitive, or already covered

Avoid custom agents when a skill or prompt rule is enough. Avoid skills when a
short project playbook is enough.

## Propose before changing

Unless the user explicitly requested a specific edit, present a concise proposal
and wait for confirmation before writing files.
