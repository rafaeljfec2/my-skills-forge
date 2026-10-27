---
name: code-quality-standards
description: >-
  Centralized hard limits and best-practice rules for TypeScript/JavaScript
  codebases — file/function size, cyclomatic and cognitive complexity,
  TypeScript strict patterns, dependency hygiene, and a copy-paste ESLint
  preset. Use when writing or refactoring TS/JS, reviewing code, or when the
  user mentions code quality, complexity, lint, Sonar, or maintainability.
  Do not use for evidence-first PR verdict (senior-code-review-judge), AppSec
  review (application-security-expert), or Snyk scan/remediate (snyk-rules).
---

# Code Quality Standards

You enforce production-grade code quality. These limits are NOT suggestions —
they are hard gates. Code that violates them is rejected.

## When not to use

- Evidence-first PR / diff verdict → `senior-code-review-judge`
- OWASP / auth / LGPD / security standards review → `application-security-expert`
- Snyk tool scan or remediate loop → `snyk-rules`
- Author implementation closeout → `principal-engineering-workflow`

## Workflow (thin orchestrator)

1. Read the target file/diff.
2. Check hard limits and refactor triggers → [references/core-rules.md](references/core-rules.md)
3. Apply TypeScript strict / async / naming / imports from the same reference.
4. Reject listed anti-patterns → [references/anti-patterns.md](references/anti-patterns.md)
5. Run the project's quality-check script if present (prefer repo-local over machine-global).
6. Report concisely: only violations and the fix (snippet, rule, refactor). No essays unless asked.

## Progressive disclosure (part of workflow)

- Deep TypeScript patterns → [references/TYPESCRIPT_RULES.md](references/TYPESCRIPT_RULES.md)
- Node.js patterns → [references/NODEJS_RULES.md](references/NODEJS_RULES.md)
- Dependency hygiene → [references/DEPENDENCY_HYGIENE.md](references/DEPENDENCY_HYGIENE.md)
- ESLint preset → [references/ESLINT_PRESET.md](references/ESLINT_PRESET.md)

## Token economy

Keep the injectable surface small. Read the reference the current step needs;
do not paste entire reference files into the reply.
