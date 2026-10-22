---
name: context-budget-guard
description: Audit every markdown file consumed by Cursor/Claude Code agents (`.cursor/rules/*.mdc`, `.cursor/skills/**/*.md`, `.claude/skills/**/*.md`, `AGENTS.md`, `CLAUDE.md`, `.github/pull_request_template.md`) and verify each one fits within its category token budget. Use when the user asks to audit context budget, check rule/skill sizes, or before publishing changes to rules/skills. Do NOT use to optimize production source code (use refactoring rule instead) or to estimate API/LLM cost.
metadata:
  version: '1.0.0'
  short-description: Enforce token-budget limits on agent-consumed markdown files
---

# Cursor Context Budget Guard

## Why this exists

Cursor injects context into every prompt:

- `alwaysApply: true` rules — injected on EVERY message of EVERY chat
- `agent_requestable` rules — injected when their trigger fires (still big when fired)
- `SKILL.md` files — injected when the skill is activated
- `AGENTS.md` / `CLAUDE.md` — injected by Cursor/Claude Code on session start

If these files grow past their budget the agent:

1. Becomes slow (more tokens to process per turn)
2. Loses recall (the actual user task is pushed out of attention)
3. Stops referencing rules automatically (Cursor truncates to fit window)
4. Costs more (each turn re-sends the entire context)

This skill audits every agent-consumed markdown file and fails fast when a budget is exceeded.

## Budgets (token approximation = bytes / 3.5)

| Category | File pattern | Budget per file | Hard ceiling |
|---|---|---|---|
| `alwaysApply` rule | `.cursor/rules/*.mdc` with `alwaysApply: true` | 3,500 tok (~12 KB) | 4,500 tok (~16 KB) |
| `agent_requestable` rule | `.cursor/rules/*.mdc` (no `alwaysApply` or `false`) | 5,000 tok (~17 KB) | 7,000 tok (~24 KB) |
| `SKILL.md` (top level) | `.cursor/skills/*/SKILL.md`, `.claude/skills/*/SKILL.md` | 2,500 tok (~9 KB) | 4,000 tok (~14 KB) |
| Skill reference doc | `.cursor/skills/**/references/*.md` | 5,000 tok (~17 KB) | 7,000 tok (~24 KB) |
| Root agent doc | `AGENTS.md`, `CLAUDE.md` | 3,000 tok (~10 KB) | 4,000 tok (~14 KB) |
| PR template | `.github/pull_request_template.md` | 2,000 tok (~7 KB) | 3,000 tok (~10 KB) |
| **Aggregate `alwaysApply` total** | sum of all `alwaysApply: true` rules | 8,000 tok (~28 KB) | 10,000 tok (~35 KB) |

> **Conversion rule**: 1 token ≈ 3.5 characters for technical markdown mixing prose + EN + code fences. This is conservative versus tiktoken `cl100k_base` (which averages 3.6–4.0 chars/tok for the same content). When the script flags a file, the real Cursor token count will be at or below the reported number — never above.

## Workflow

### 1) Run the audit

```bash
python .cursor/skills/context-budget-guard/scripts/audit_budget.py
```

Optional flags:

| Flag | Effect |
|---|---|
| `--root <path>` | Repo root (default: cwd) |
| `--ceiling` | Compare against the hard ceiling instead of the soft budget (CI mode) |
| `--json` | Emit machine-readable JSON instead of the table |
| `--only <category>` | Audit a single category (`always`, `requestable`, `skill`, `reference`, `root`, `pr_template`) |
| `--fail-on warn` | Exit non-zero on warnings too (default: only on errors) |

Exit codes:

- `0` — every file within budget
- `1` — at least one file ≥ ceiling (HARD violation)
- `2` — at least one file ≥ soft budget but < ceiling (WARNING) — only when `--fail-on warn`

### 2) Read the report

The script prints a table grouped by category, each row showing:

- File path (relative)
- Bytes
- Estimated tokens
- Budget
- Margin (`+` headroom / `-` overage)
- Status: `OK` / `WARN` / `FAIL`

A summary footer reports:

- Aggregate `alwaysApply` token sum vs. its dedicated budget
- Counts: `OK / WARN / FAIL`

### 3) Act on violations

When a file fails (or warns close to ceiling), apply ONE of these patterns — never just truncate:

| Symptom | Action |
|---|---|
| `alwaysApply` rule oversized | Split into `<name>-core.mdc` (alwaysApply, axioms+limits only) + `<name>-detail.mdc` (agent_requestable, workflow detail). Add the trigger to the core's "Mandatory Sub-Rules" table. |
| `agent_requestable` rule oversized | Same split: extract the largest section (usually examples, anti-patterns, or templates) into a sibling sub-rule with a narrower trigger. |
| `SKILL.md` oversized | Move long examples, reference tables, schema dumps into `references/<topic>.md` and have `SKILL.md` link to them via `<path>` (Anthropic skill convention). Keep `SKILL.md` to: overview, workflow steps, failure handling. |
| Reference doc oversized | Split by topic (e.g., `references/auth.md` + `references/guards.md`). |
| `AGENTS.md` / `CLAUDE.md` oversized | Move project-specific deep dives into `docs/` and link from the root file. Root file should be navigation + quick-start only. |
| PR template oversized | Collapse optional sections into `<details>` blocks; remove sub-bullets that repeat the section heading. |

After splitting, re-run the audit to confirm. NEVER mark a file as "won't fix" — the budget exists for a reason (Cursor truncates silently otherwise).

### 4) Wire into CI / pre-push (optional but recommended)

Add to `.github/workflows/ci.yml` (new job):

```yaml
context-budget:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v5
      with:
        python-version: '3.11'
    - name: Audit agent context budget
      run: python .cursor/skills/context-budget-guard/scripts/audit_budget.py --ceiling --fail-on warn
```

Add to `.husky/pre-push` (after the format check):

```bash
python .cursor/skills/context-budget-guard/scripts/audit_budget.py --ceiling || {
  echo ""
  echo "Context budget violation. Run:"
  echo "  python .cursor/skills/context-budget-guard/scripts/audit_budget.py"
  echo "to see details, then split oversized files (see SKILL.md § 3)."
  exit 1
}
```

## When to run manually

- After editing any `.mdc` rule
- After editing any `SKILL.md`
- Before opening a PR that touches `.cursor/`, `.claude/`, `AGENTS.md`, `CLAUDE.md`, or `.github/pull_request_template.md`
- After bulk-importing skills/rules from another project

## Failure handling

| Failure | Action |
|---|---|
| `python` missing | Stop. Ask user to install Python 3.9+ (script uses stdlib only). |
| Script not found | Stop. Verify the skill is installed at `.cursor/skills/context-budget-guard/`. |
| File counted that should be ignored (e.g., `node_modules`) | Add the path to `IGNORED_DIRS` constant in the script — do not silently exclude via wildcard. |
| Budget feels wrong for a category | Re-evaluate the budget table at the top of this file with evidence (Cursor docs, observed truncation). Update the script's `BUDGETS` dict to match. Never patch a single file's status — change the budget. |

## Anti-patterns (do NOT do)

- "Just delete some lines to fit" — first try splitting by responsibility (sub-rule, references/).
- Move examples into source code as comments — comments belong to code intent, not skill documentation.
- Increase the budget per file to hide an offender — the budget is an architectural constraint.
- Run the audit only in CI — Cursor truncates the moment you save the file, not when CI runs. Run locally before each commit touching agent docs.
