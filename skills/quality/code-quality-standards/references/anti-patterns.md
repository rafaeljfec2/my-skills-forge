# Anti-patterns — reject on sight

Hard rejects for TypeScript/JavaScript when enforcing `code-quality-standards`:

- `any`, `as any`, `// @ts-ignore`, `// @ts-nocheck`.
- `||` for defaults (use `??`).
- Mutable props (props without `Readonly<>`).
- `enum` (use const object + literal union).
- Functions returning `void` that throw (return `Result<T, E>` or document throw behavior in name).
- Catch blocks that swallow errors silently.
- Nested ternaries (extract to if/else or named function).
- Long parameter lists (>4) — use options object.
- Boolean parameters (use enum/literal union for clarity at call site).
- `for` + index when `for...of` or `.map`/`.filter` express intent better.
- Comments that restate the code (`// increment counter`).
