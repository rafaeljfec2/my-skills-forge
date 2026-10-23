# TypeScript Rules - Deep Reference

Loaded on demand. Patterns for rigorous TypeScript codebases.

## Type vs interface

- `interface` for object shapes that may be extended/implemented (DTOs, contracts, public APIs).
- `type` for unions, intersections, mapped types, conditional types, function types.
- Be consistent within a module.

## Branded types - prevent primitive mixing

```ts
type Brand<T, B> = T & { readonly __brand: B };

type UserId = Brand<string, 'UserId'>;
type Email = Brand<string, 'Email'>;

function makeEmail(raw: string): Email {
  if (!/^.+@.+\..+$/.test(raw)) throw new Error('Invalid email');
  return raw as Email;
}

function sendEmail(to: Email, subject: string) { /* ... */ }

const id: UserId = '123' as UserId;
sendEmail(id, 'Hi'); // compile error - cannot pass UserId where Email expected
```

Use for IDs, timestamps, money amounts, currencies, anything where mixing same-primitive values is a real bug class.

## Exhaustive switch

```ts
type Status = 'pending' | 'active' | 'archived';

function statusLabel(s: Status): string {
  switch (s) {
    case 'pending': return 'Pending';
    case 'active': return 'Active';
    case 'archived': return 'Archived';
    default: {
      const _exhaustive: never = s;
      throw new Error(`Unhandled status: ${String(_exhaustive)}`);
    }
  }
}
```

If you add a new status to the union, the `never` assignment fails at compile time. This is your safety net.

## Result/Either type - explicit error handling

```ts
type Result<T, E> =
  | { ok: true; value: T }
  | { ok: false; error: E };

async function fetchUser(id: UserId): Promise<Result<User, 'NotFound' | 'Network'>> {
  try {
    const res = await api.get(`/users/${id}`);
    if (res.status === 404) return { ok: false, error: 'NotFound' };
    return { ok: true, value: res.data };
  } catch {
    return { ok: false, error: 'Network' };
  }
}

const r = await fetchUser(id);
if (!r.ok) {
  if (r.error === 'NotFound') return notFound();
  return serverError();
}
const user = r.value; // narrowed to User
```

Use this when callers MUST handle errors. Reserve thrown errors for unrecoverable states (programmer errors, OOM).

## Generic constraints

```ts
function getProperty<T, K extends keyof T>(obj: T, key: K): T[K] {
  return obj[key];
}
```

Constrain generics to the minimum required structure. Prefer `extends` constraints over bare `T`.

## `satisfies` - typed but inferred

```ts
const config = {
  host: 'localhost',
  port: 3000,
  features: ['auth', 'logs'],
} satisfies AppConfig;

config.features[0]; // typed as 'auth' | 'logs', not string
```

`as` widens loses information. `satisfies` validates without widening.

## Const assertions

```ts
const ROLES = ['admin', 'user', 'viewer'] as const;
type Role = (typeof ROLES)[number]; // 'admin' | 'user' | 'viewer'
```

Replaces enum for literal unions with runtime list.

## Discriminated unions

```ts
type Action =
  | { type: 'increment'; by: number }
  | { type: 'reset' }
  | { type: 'set'; value: number };

function reducer(state: number, action: Action): number {
  switch (action.type) {
    case 'increment': return state + action.by;
    case 'reset': return 0;
    case 'set': return action.value;
  }
}
```

Each arm is fully typed. Avoid `Partial<>` and optional fields when discriminated unions express intent better.

## Mapped + conditional types - sparingly

Powerful but expensive in compile time and read time. Use when:
- Building reusable utility types (`DeepReadonly<T>`).
- Generating API client types from contracts.

Avoid for one-off transformations - inline expansion is clearer.

## Type guards

```ts
function isError(value: unknown): value is Error {
  return value instanceof Error;
}

function isUser(value: unknown): value is User {
  return (
    typeof value === 'object' &&
    value !== null &&
    'id' in value &&
    'email' in value
  );
}
```

For complex shapes, prefer Zod parsing - it gives you both validation and the type.

## Zod for boundary validation

```ts
const userSchema = z.object({
  id: z.string().uuid(),
  email: z.string().email(),
  age: z.number().int().min(0),
});

type User = z.infer<typeof userSchema>;

const user = userSchema.parse(rawJson); // throws on invalid
const result = userSchema.safeParse(rawJson); // returns { success, data } | { success, error }
```

Use Zod at every boundary (HTTP req/res, env vars, message queue payloads, file IO).

## strictNullChecks discipline

- Distinguish `null` (intentionally absent) from `undefined` (not yet set).
- Functions return `T | null` for "looked up, not found"; `T | undefined` for "did not look".
- Optional fields use `?:` (yields `undefined`); never `?: T | null` unless both states matter.

## `Readonly<>` everywhere it makes sense

- All function parameters that the function does not mutate.
- All return types that callers should not mutate.
- All component props (`Readonly<{...}>`).
- Arrays: `ReadonlyArray<T>` or `readonly T[]`.

## Avoid `Function`, `Object`, `{}`

These are too broad. Use specific types: `(args) => ret`, `Record<string, unknown>`, `unknown`.

## `noUncheckedIndexedAccess: true`

Forces you to handle the `undefined` case for `array[i]` and `obj[key]`. Annoying at first, prevents real bugs.

```ts
const first = users[0]; // type: User | undefined
if (first) { /* ... */ }
```

## Module boundaries

- Export types from `index.ts` of each module - they are part of the public API.
- Internal types stay in their feature folder.
- Use `import type` for type-only imports - improves tree-shaking and avoids cycles.
