---
name: code-quality-standards
description: >-
  Centralized hard limits and best-practice rules for TypeScript/JavaScript
  codebases — file/function size, cyclomatic and cognitive complexity,
  TypeScript strict patterns, dependency hygiene, and a copy-paste ESLint
  preset. Use when writing or refactoring TS/JS, reviewing code, or when the
  user mentions code quality, complexity, lint, Sonar, or maintainability.
---

# Code Quality Standards

You enforce production-grade code quality. These limits are NOT suggestions —
they are hard gates. Code that violates them is rejected.

## Workflow (thin orchestrator)

1. Read the target file/diff.
2. Check hard limits and refactor triggers → [references/core-rules.md](references/core-rules.md)
3. Apply TypeScript strict / async / naming / imports from the same reference.
4. Run the project's quality-check script if present (prefer repo-local over machine-global).
5. Report concisely: only violations and the fix.

## Progressive disclosure (part of workflow)

- For deep TypeScript patterns (branded types, exhaustive checks, generic constraints, Result types, satisfies, type vs interface): see [references/TYPESCRIPT_RULES.md](references/TYPESCRIPT_RULES.md)
- For Node.js patterns (error cause chains, signal handling, async pitfalls, no `process.exit` in libs): see [references/NODEJS_RULES.md](references/NODEJS_RULES.md)
- For dependency management (evaluating new deps, audit, peer deps, deduplication, freshness): see [references/DEPENDENCY_HYGIENE.md](references/DEPENDENCY_HYGIENE.md)
- For ESLint preset ready to copy into `.eslintrc.cjs`: see [references/ESLINT_PRESET.md](references/ESLINT_PRESET.md)

## Anti-patterns - reject on sight

- `any`, `as any`, `// @ts-ignore`, `// @ts-nocheck`.
- `||` for defaults (use `??`).
- Mutable props (props without `Readonly<>`).
- `enum` (use const object + literal union).
- Functions returning `void` that throw (return `Result<T, E>` or document throw behavior in name).
- Catch blocks that swallow errors silently.
- Nested ternaries (extract to if/else or named function).
- Long parameter lists (>4) - use options object.
- Boolean parameters (use enum/literal union for clarity at call site).
- `for` + index when `for...of` or `.map`/`.filter` express intent better.
- Comments that restate the code (`// increment counter`).

## Output style

- Show the violating snippet, the rule it breaks, the refactored version. That is all.
- No essays. No extensive explanation unless asked.

## Token economy

Keep the injectable surface small. Read the reference the current step needs;
do not paste entire reference files into the reply.
