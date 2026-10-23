# STFlow profile checks

Apply only when STEP 0 detects STACK PROFILE = STFlow
(`apps/api/drizzle.config.ts` and `pnpm-workspace.yaml` with `apps/*`).

## Mechanical (STEP 2)

Also run `pnpm budget:strict` and `pnpm budget:test` when local. Include Budget in the MECHANICAL block.

## Entry points (STEP 3)

When identifying what a guard protects, prefer concrete STFlow examples (e.g. `tenantId` filter on call recordings). Search patterns for Drizzle writes and Nest entry points are in [scans.md](scans.md).

## Test adequacy (STEP 4)

For Drizzle: override `DRIZZLE_PROVIDER` with a test double, or stub the chain
(`db.insert(table).values(...).returning()`) returning realistic rows. `[]`
cannot prove the new behavior runs.

## File-by-file (STEP 5)

- Flag `db.execute(sql.raw(...))` and interpolated `sql\`${userInput}\`` as IDOR/SQLi risk.
- Require `tenantId` filter on every multi-tenant query; check IDOR on `:id` route params.
- Migrations in `apps/api/drizzle/*.sql`: rollback-safe; defaults on `NOT NULL` adds; index on every FK; intentional cross-tenant CASCADE; RLS aligned with `0046_rls_foundation.sql`.
- Imports from `@stflow/shared/*` (no deep relatives like `../../../shared`).
- Frontend: ternary with `null` (never `&&`); mobile-first; adherence to `apps/web/DESIGN.md` — flag raw literals (`bg-[#hex]`, `p-[12px]`), raw utilities vs tokens, variants outside §8.
- Performance: prefer Drizzle `with` / `leftJoin` over loop-then-query.

## Cross-validation (STEP 6)

Docs sync: for every modified `apps/api/src/modules/<x>/**` or
`apps/web/src/features/<x>/**` path, the matching `docs/modules/<x>.md` or
`docs/features/<x>.md` must appear in the diff (with advanced `last_verified`
header) OR the PR body must justify no-change. Same for cross-cutting
`docs/architecture/*.md` themes (auth, multi-tenancy, esocial, messaging).
