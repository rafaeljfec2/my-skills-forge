---
name: cognitive-complexity-guard
description: Keeps Sonar-friendly cognitive complexity low (TypeScript/JavaScript). Use when writing or refactoring functions, hooks, services, or when Sonar reports typescript:S3776, deep nesting S2004, or similar.
---

# Cognitive complexity guard

## Target

- Prefer **small functions** with a **single responsibility**.
- Keep **Sonar cognitive complexity ≤ 15** per function (adjust if your quality gate differs).
- Avoid **deep nesting** (flatten with early returns, extracted helpers, or `switch` + small `case` bodies).

## Patterns

1. **Early returns** instead of wrapping the whole body in `if (ok) { … }`.
2. **Extract** branches into named functions: `parseX`, `handleY`, `buildZ`, `assertOk`.
3. **Replace long `if/else` chains** with `switch (discriminant)` where each case delegates to a one-purpose function.
4. **Hooks (`useChatStream`, services)**: move SSE parsing, API branches (e.g. Cursor vs Claude), and persistence into **separate modules** or **private class methods** with narrow types.
5. **Loops**: move body logic to `processItem(item)`; keep the loop line count minimal.
6. **Tests**: avoid `class` implementing `PromiseLike` with `then` (Sonar S7739); use a **factory** returning a plain object if a thenable mock is required.

## Do not

- Add `eslint-disable` / `NOSONAR` solely to silence complexity without refactoring.
- Grow a "god" function beyond ~50 lines without splitting.

## Verify

After refactors, run the project linter and Sonar (or IDE Sonar rules) on touched files.
