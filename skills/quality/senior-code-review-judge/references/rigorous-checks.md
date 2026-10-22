# Senior Code Reviewer — Rigorous Lens

Deep technical lens applied AFTER mechanical/entry-point/test-adequacy steps. Goal: catch issues that lint and tests cannot — design quality, maintainability, architectural fit.

## 1. Intent comprehension (mandatory; do FIRST)

Before criticizing anything, restate the change to prove understanding:

```
RIGOROUS LENS — INTENT
Restated intent (2-3 sentences in own words):
  <what the author actually changed and why>
Hidden assumption:
  <invariant the change relies on; e.g., "assumes tenantId is always present in request">
Trade-off identified:
  <what was gained vs. what was given up; e.g., "gained perf via cache, lost real-time accuracy">
Alignment check:
  PR title/body says X → diff implements Y → match? <YES | NO; explain>
```

If you cannot restate the change clearly, you do not understand it — re-read before judging.

## 2. Correctness deep-dive

Tests proving "happy path passes" is the floor. The reviewer's job is the ceiling:

- **Invariants**: what MUST be true before AND after the operation? Is it preserved?
- **Contracts**: explicit pre/post-conditions? Defensive guards on inputs from untrusted boundary (HTTP, queue payload, third-party API)?
- **Edge cases checklist**: empty `[]`, `null`, `undefined`, `0`, negative numbers, `Number.MAX_SAFE_INTEGER`, very large strings, Unicode/emoji, concurrent calls, partial failures, network timeout, retry storm
- **Race conditions** (async): shared state mutated without lock? `await` missing in middle of sequence?
- **Idempotency** (workers/handlers): replaying the same job twice produces the same result?
- **Atomicity** (DB): multi-step writes inside a transaction? Compensating action on failure?
- **Resource cleanup**: subscriptions unsubscribed, intervals cleared, connections returned to pool, file descriptors closed?
- **Error propagation**: thrown errors actually reach the right boundary (try/catch swallowing? `.catch(() => {})`?)

## 3. Code smells (refactor opportunities)

Flag and suggest the refactor explicitly. Cite Fowler's catalog where applicable:

| Smell | Trigger | Suggested refactor |
|---|---|---|
| Long Method | > 30 LOC body | Extract Method |
| Long Parameter List | > 4 positional params | Introduce Parameter Object / Builder |
| Long Class / God Object | > 800 LOC or > 15 public methods | Extract Class / Module |
| Feature Envy | method uses other class's data more than its own | Move Method |
| Primitive Obsession | bare `string`/`number` for domain concepts (e.g., `tenantId: string`) | Branded types / Value Object |
| Switch Statement | switch on type/enum that drives behavior | Replace Conditional with Polymorphism / Strategy |
| Data Clumps | 3+ fields always travel together | Extract Object |
| Shotgun Surgery | a logical change requires edits across many unrelated files | Move Field/Method to consolidate |
| Magic Number/String | `if (x > 86400)` | Extract Constant |
| Duplicated Code | same shape twice | Extract Function (after 2nd repetition; Rule of Three for early extraction) |
| Comments explaining WHAT | code unclear → comment compensates | Rename + Extract Method until comment is redundant |
| Dead Code | unreferenced exports/private methods | Remove |

## 4. Design patterns (use when applicable, flag when missing)

Reviewer should suggest a pattern when its absence creates the smell:

- **Strategy**: variant algorithms selected at runtime → replaces `switch` on `kind`
- **Factory**: complex/conditional construction → `static create(input): Service`
- **Repository**: encapsulates DB access; service layer never sees the ORM client directly (e.g., Drizzle `db.*`, Prisma `prisma.*`)
- **Adapter**: third-party SDK integration with our domain interface
- **Observer / EventEmitter**: decoupled notification (NestJS `@nestjs/event-emitter`)
- **Decorator**: cross-cutting concerns (NestJS `@UseGuards`, `@Roles`, custom `@Transactional`)
- **DTO + Validator**: every controller boundary uses a DTO validated by Zod or `class-validator` (never raw `req.body`)
- **Dependency Injection**: constructor-injected interfaces, not concrete classes (testability)
- **Module boundary** (NestJS): cross-module access only via the module's exported provider, never deep-imports
- **Specification pattern**: complex query criteria reused in multiple repositories

Flag both **wrong pattern applied** (e.g., Singleton where Transient was needed) and **pattern missing** (e.g., 6-branch `switch` should be Strategy).

## 5. TypeScript + typescript-eslint (v7+) checklist

Beyond `no-explicit-any`, validate these strict rules are honored in the diff:

- `@typescript-eslint/strict-boolean-expressions` — no `if (str)` for nullable strings; force `if (str !== undefined && str !== "")`
- `@typescript-eslint/no-unsafe-{assignment,member-access,call,return,argument}` — `any` cannot leak across boundaries
- `@typescript-eslint/no-floating-promises` — every `Promise` awaited, returned, or `.catch(...)`-handled
- `@typescript-eslint/no-misused-promises` — no async function passed to a non-Promise-aware callback (e.g., array methods, event handlers expecting `void`)
- `@typescript-eslint/await-thenable` — no `await` on a non-Promise value
- `@typescript-eslint/return-await` — `return await` only when needed for try/catch wrapping
- `@typescript-eslint/prefer-nullish-coalescing` — `??` not `||` (aligns with user rule)
- `@typescript-eslint/prefer-optional-chain` — `a?.b?.c` over `a && a.b && a.b.c`
- `@typescript-eslint/no-non-null-assertion` — no `!` postfix
- `@typescript-eslint/consistent-type-imports` — `import type { X }` for type-only imports
- `@typescript-eslint/explicit-function-return-type` — public APIs (controllers, services, exported funcs)
- `@typescript-eslint/prefer-readonly` — class fields not reassigned must be `readonly`
- `@typescript-eslint/no-unnecessary-type-assertion` — assertion already known by inference
- `@typescript-eslint/switch-exhaustiveness-check` — `switch` over union/enum must be exhaustive (with `never` default)
- **Sonar** `typescript:S6759` — props of React components must be `readonly` (aligns with user rule)
- **Sonar** `typescript:S3776` — cognitive complexity ≤ 15 per function

If the diff visibly violates any of these AND CI lint passes, ESLint config is permissive — flag as IMPORTANT in the verdict ("ESLint config does not enforce <rule>; new code introduces violation that CI cannot catch").

## 6. Architectural rigor

- **Cohesion**: does each function or class do one thing? Split anything with more than one responsibility.
- **Coupling**: do dependencies go through an interface rather than a concrete implementation? Is construction injected?
- **Boundaries (clean architecture)**: domain stays independent of infrastructure (an ORM client such as Drizzle or Prisma never belongs in the domain layer). The use case orchestrates. The adapter integrates.
- **Testability**: mocking points are interfaces, not concrete classes. No buried `new ConcreteService()`.
- **Scalability**: does the hot path have a cache? Does the number of database calls grow with input size (N+1)? Is batching applicable?
- **Observability**: structured logs on error paths? A span or trace on cross-service operations? Metrics on paths that matter for the SLO?
- **Backwards compatibility**: is an API change opt-in (additive) or breaking? Is the deprecation path documented?
- **Configurability**: are hardcoded values that should come from env or config left in code? Is there a feature flag for a gradual rollout?

## 7. Final print

Append to STEP 7 verdict block:

```
RIGOROUS LENS:
Intent restated: <one line>
Hidden assumption: <one line>
Smells found: <count>; key items: [...]
Patterns missing/violated: [...]
TS/ESLint config gaps: [...]   # rules CI doesn't enforce but should
Architectural concerns: [...]
```

If RIGOROUS LENS surfaces issues missed in Steps 2-5, lift them into the appropriate severity bucket (CRITICAL-* / IMPORTANT / MINOR) before emitting the verdict.
