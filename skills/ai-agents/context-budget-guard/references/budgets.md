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
