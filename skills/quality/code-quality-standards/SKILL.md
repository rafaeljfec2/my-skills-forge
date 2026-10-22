---
name: code-quality-standards
description: Centralized hard limits and best-practice rules for TypeScript/JavaScript codebases - file/function size, cyclomatic and cognitive complexity, TypeScript strict patterns, dependency hygiene, and a copy-paste ESLint preset. Use when writing or refactoring any TS/JS code, when reviewing code, or when the user mentions code quality, refactor, complexity, lint, typecheck, best practices, dependency hygiene, ESLint, Sonar, or maintainability.
---

# Code Quality Standards

You enforce production-grade code quality. These limits are NOT suggestions - they are hard gates. Code that violates them is rejected.

## Hard limits (Sonar-aligned)

| Metric | Limit | Where enforced |
|---|---|---|
| Lines per file | <= 500 | ESLint `max-lines`, `quality-check.sh` |
| Lines per function | <= 40 | ESLint `max-lines-per-function` |
| Function parameters | <= 4 | ESLint `max-params` |
| Nesting depth | <= 3 | ESLint `max-depth` |
| Cyclomatic complexity | <= 10 | ESLint `complexity` (Sonar S1541) |
| Cognitive complexity | <= 15 | ESLint `sonarjs/cognitive-complexity` (Sonar S3776) |
| Statements per function | <= 25 | ESLint `max-statements` |

When you hit a limit, REFACTOR. Do NOT bump the threshold.

## Refactor triggers

| Signal | Action |
|---|---|
| File > 400 lines (warning at 80%) | Split by responsibility (extract module) |
| Function > 30 lines (warning at 75%) | Extract helper functions |
| 5+ params | Group into a `Readonly<>` options object |
| 3+ duplications across files | Extract shared utility/component |
| Function with cognitive >= 12 | Flatten branches; replace nested if/else with early returns or polymorphism |
| Imports >15 in a single file | File is doing too much; split by feature |

## Cognitive complexity how-to

When flattening a function that hits Sonar S3776 (or nesting S2004):

1. Prefer **early returns** instead of wrapping the whole body in `if (ok) { … }`.
2. **Extract** branches into named functions: `parseX`, `handleY`, `buildZ`, `assertOk`.
3. Replace long `if/else` chains with `switch (discriminant)` where each case delegates to a one-purpose function.
4. In hooks and services, move parsing, API branches, and persistence into **separate modules** or **private methods** with narrow types.
5. In loops, move body logic to `processItem(item)`; keep the loop itself short.
6. In tests, avoid a `class` implementing `PromiseLike` with `then` (Sonar S7739); use a **factory** that returns a plain thenable object.

Do **not** add `eslint-disable` / `NOSONAR` solely to silence complexity without refactoring. Do not grow a "god" function beyond ~50 lines without splitting. After refactors, run the project linter and Sonar (or IDE Sonar rules) on touched files.

## TypeScript strict - non-negotiable

1. **Never `any`**. Use `unknown` and narrow, or define a proper type.
2. **Never `||` for default values** - use `??` so `0`, `''`, `false` are preserved.
3. **Props are `Readonly<>`** - apply `Readonly<{...}>` on every component prop interface (sonarqube `typescript:S6759`).
4. **Avoid `enum`** - prefer `const` object + union of literals (`as const`):
   ```ts
   const UserRole = { Admin: 'admin', User: 'user' } as const;
   type UserRole = (typeof UserRole)[keyof typeof UserRole];
   ```
5. **Use `satisfies`** for typed literals that need inference:
   ```ts
   const config = { host: 'localhost', port: 3000 } satisfies ServerConfig;
   ```
6. **Exhaustive switches** with `never` check (see TYPESCRIPT_RULES.md).
7. **No `as` casts** unless absolutely necessary - prefer type guards.
8. **No comments narrating code** - code must be self-documenting via naming. Only document non-obvious intent.
9. **No `console.log`** - use the project's logger.
10. **Strict tsconfig**: `strict: true`, `noUncheckedIndexedAccess: true`, `noImplicitOverride: true`, `exactOptionalPropertyTypes: true`.

## Async patterns

- `Promise.all` for independent calls.
- `Promise.allSettled` when partial failure should not block.
- `Promise.race` only for first-result-wins.
- Sequential `await` ONLY when later calls depend on earlier results.
- Always handle errors - either via try/catch or by returning a Result/Either type.

## Naming

- Variables and functions: `camelCase`.
- Types and interfaces: `PascalCase`.
- Constants: `UPPER_SNAKE_CASE` only for true constants (env, magic numbers); `camelCase` for module-level config.
- Booleans: `is*`, `has*`, `should*`, `can*`, `did*`.
- Event handlers: `handle*` (in component) or `on*` (when received as prop).
- Files: `kebab-case.ts` for backend; component files mirror their default export name.
- Tests: `<file-under-test>.spec.ts`. Description in English.

## Imports order

```ts
// 1. Node built-ins
import { readFileSync } from 'node:fs';
// 2. External packages
import { z } from 'zod';
import express from 'express';
// 3. Internal aliases (@/...)
import { logger } from '@/infrastructure/logger';
// 4. Relative parent
import { UserMapper } from '../mappers/user-mapper';
// 5. Relative same-dir
import { schema } from './schema';
// 6. Type-only (separate group, marked with `type` keyword)
import type { User } from '@/domain/user';
```

ESLint `import/order` enforces this.

## When invoked, follow this workflow

1. **Read the target file/diff** to understand the change.
2. **Check against the hard limits table** - file size, function size, complexity. If violated, REFACTOR before proceeding.
3. **Apply TypeScript strict rules** - replace `any`, `||`, missing `Readonly<>`.
4. **Run `~/.cursor/scripts/quality-check.sh`** if available in the project to validate externally (does not consume context).
5. **Report concisely**: only mention violations and the fix. No prose.

## Progressive disclosure - load only what you need

- For deep TypeScript patterns (branded types, exhaustive checks, generic constraints, Result types, satisfies, type vs interface): see [TYPESCRIPT_RULES.md](TYPESCRIPT_RULES.md)
- For Node.js patterns (error cause chains, signal handling, async pitfalls, no `process.exit` in libs): see [NODEJS_RULES.md](NODEJS_RULES.md)
- For dependency management (evaluating new deps, audit, peer deps, deduplication, freshness): see [DEPENDENCY_HYGIENE.md](DEPENDENCY_HYGIENE.md)
- For ESLint preset ready to copy into `.eslintrc.cjs`: see [ESLINT_PRESET.md](ESLINT_PRESET.md)

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
