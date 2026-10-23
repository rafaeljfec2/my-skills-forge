# Node.js Rules - Deep Reference

Loaded on demand. Production patterns for Node.js services.

## Error handling - use cause chains

```ts
try {
  await processOrder(order);
} catch (error) {
  throw new Error(`Failed to process order ${order.id}`, { cause: error });
}
```

`Error.cause` (ES2022) preserves the original error for diagnostics. Loggers should walk the chain.

## Custom error classes - hierarchical

```ts
export class DomainError extends Error {
  readonly name = 'DomainError';
  constructor(message: string, options?: ErrorOptions) {
    super(message, options);
  }
}

export class NotFoundError extends DomainError {
  readonly name = 'NotFoundError';
  constructor(resource: string, id: string, options?: ErrorOptions) {
    super(`${resource} not found: ${id}`, options);
  }
}
```

Catch by type, not by message string.

## Never `process.exit` in libs/services

`process.exit` skips cleanup (open file handles, sockets, in-flight requests). Reserve for top-level CLI/main only.

```ts
// BAD inside a library
if (!config.host) process.exit(1);

// GOOD
if (!config.host) throw new ConfigError('host is required');
```

## Signal handling - graceful shutdown

```ts
async function main() {
  const server = await startServer();

  const shutdown = async (signal: NodeJS.Signals) => {
    logger.info({ signal }, 'shutdown initiated');
    server.close();
    await drainQueues();
    await closeDb();
    logger.info({ signal }, 'shutdown complete');
    process.exit(0);
  };

  process.on('SIGTERM', () => void shutdown('SIGTERM'));
  process.on('SIGINT', () => void shutdown('SIGINT'));
}
```

Always handle SIGTERM (Kubernetes/Docker stop), SIGINT (Ctrl+C). Set a timeout for forceful exit if drain takes too long (>30s).

## Async/await pitfalls

### Sequential vs parallel

```ts
// BAD - sequential when calls are independent
const user = await fetchUser(id);
const posts = await fetchPosts(id);

// GOOD
const [user, posts] = await Promise.all([fetchUser(id), fetchPosts(id)]);
```

### Forgotten awaits leak promises

```ts
// BAD - throws unhandled rejection
async function save(items: Item[]) {
  items.forEach(item => repo.save(item)); // promises lost
}

// GOOD
async function save(items: Item[]) {
  await Promise.all(items.map(item => repo.save(item)));
}
```

### Never mix `.then` with `await` in the same function

Pick one style per function for readability.

## Promise concurrency control

For large item counts, do NOT `Promise.all` everything (overwhelms the target):

```ts
import pLimit from 'p-limit';
const limit = pLimit(5);

await Promise.all(items.map(item => limit(() => process(item))));
```

## Logging - structured, not strings

Use the project's logger (pino, winston). NEVER `console.log`.

```ts
// Format: logger.<level>({ ...context }, message)
logger.info({ userId: user.id, action: 'login' }, 'user signed in');
logger.error({ err: error, orderId }, 'order processing failed');
```

Never log secrets (passwords, tokens, full credit card numbers, full SSN). Mask in middleware before logging.

## HTTP client patterns

- Always set timeouts (no infinite hangs): `axios.create({ timeout: 10_000 })`.
- Always set max retries with exponential backoff for transient failures.
- Never retry non-idempotent requests (POST without idempotency key).
- Use circuit breaker (`opossum`) for unstable dependencies.
- Always validate responses (do not trust upstream shape).

## Streams over buffers for large payloads

```ts
// BAD - loads entire file in memory
const data = await readFile('/path/to/big.csv');

// GOOD
import { pipeline } from 'node:stream/promises';
import { createReadStream } from 'node:fs';
import { createGunzip } from 'node:zlib';

await pipeline(
  createReadStream('/path/to/big.csv.gz'),
  createGunzip(),
  parseCsv(),
  saveToDb(),
);
```

## Worker threads for CPU-heavy work

Node is single-threaded for JS. CPU-bound work (image processing, JSON parsing of >10MB, crypto) blocks the event loop. Offload to `worker_threads`.

## Configuration

- All env vars validated at startup with Zod schema.
- Fail fast at boot if config invalid - never run with partial config.
- No env access scattered across the codebase - centralize in `config/index.ts`.

```ts
const envSchema = z.object({
  NODE_ENV: z.enum(['development', 'staging', 'production']),
  PORT: z.coerce.number().int().positive().default(3000),
  DATABASE_URL: z.string().url(),
});

export const env = envSchema.parse(process.env);
```

## Dependency injection

Use a container (tsyringe, awilix, inversify) for non-trivial apps. Avoids:
- Global singletons that are hard to test.
- Hidden dependencies inside functions.
- Module-load-time side effects.

Constructor injection > setter injection.

## Date/time

- Always use UTC internally.
- Convert to user timezone only at the presentation boundary.
- Use `date-fns` (or `Temporal` when widely available) - never `moment`.
- Compare timestamps as numbers (`getTime()`) or via library helpers, never strings.

## File paths

- Use `node:path` for joining: `path.join(rootDir, 'config', 'app.json')`.
- Never concatenate strings with `/`.
- Use `node:url` `fileURLToPath(import.meta.url)` for ESM `__dirname` equivalent.

## ESM vs CommonJS

- New projects: ESM (`"type": "module"`).
- Mixed projects: be explicit with `.cjs` and `.mjs` when the package type is ambiguous.
- Avoid dual packaging unless you publish a library.

## Resource cleanup

Always release resources:

```ts
const fileHandle = await fs.open(path, 'r');
try {
  // use handle
} finally {
  await fileHandle.close();
}
```

For multiple resources: use Symbol.asyncDispose pattern (Node 22+) or explicit cleanup stacks.

## Testing

- Unit tests: pure functions, no IO.
- Integration tests: against real DB/queue (use testcontainers).
- E2E: against deployed staging, smoke only.
- Mock at the adapter boundary, not at the function boundary.
- One assertion per test (or grouped via `expect.objectContaining`).

## Performance basics

- Profile before optimizing (`node --prof`, clinic.js).
- Avoid synchronous file IO in request handlers.
- Cache compiled regex outside hot loops.
- Reuse HTTP agents/clients - do not create per request.
