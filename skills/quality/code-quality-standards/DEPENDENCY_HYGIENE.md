# Dependency Hygiene

Loaded on demand. How to evaluate, add, audit, and maintain dependencies.

## Before adding a new dependency - the 8-question checklist

1. **Is this in the standard library?** (`node:fs/promises`, `Intl`, `crypto.randomUUID`, structuredClone, etc.)
2. **Do we already have a similar dep?** (`pnpm list <topic>` and grep imports first)
3. **Is the package actively maintained?** (last release within 6 months; open issues addressed)
4. **What is the bundle size impact?** (https://bundlephobia.com - reject if >50 KB gzipped without strong justification)
5. **What is the dependency tree size?** (avoid packages that pull >100 transitive deps for a small feature)
6. **Is the maintainer reputable?** (org-backed, recognized contributor, > 1M downloads/week, multiple maintainers)
7. **Does it have a permissive license?** (MIT, ISC, Apache-2, BSD - reject AGPL/SSPL unless intended)
8. **Are there known CVEs?** (`npm audit` / Snyk / `pnpm audit` before installing)

If you cannot answer YES to most, do not add the dep.

## Versioning - pin or range?

| Type | Strategy |
|---|---|
| App / service | `~1.2.3` (patch only) for direct deps. Use lockfile for transitive. |
| Library | `^1.2.3` (compatible) for runtime deps. `peerDependencies` for shared types/frameworks. |
| Build tools | exact pin (`1.2.3`) - reproducibility critical |

Never use `*`, `latest`, or `>=`. Always lock with the package manager's lockfile (`pnpm-lock.yaml`, `package-lock.json`, `yarn.lock`).

## Auditing

Run regularly:

```bash
pnpm audit --prod         # production deps only (what ships)
pnpm audit                # all deps
pnpm outdated             # see what is behind
```

CI must run `pnpm audit --prod` and fail on high/critical.

## Override transitive vulns (pnpm)

When a transitive dep is vulnerable but you cannot upgrade the parent:

```json
{
  "pnpm": {
    "overrides": {
      "axios@<1.15.1": "1.15.1",
      "follow-redirects@<1.16.0": "1.16.0",
      "handlebars@<4.7.9": "4.7.9"
    }
  }
}
```

Document each override with the CVE id in a comment-like file (`docs/security-overrides.md`) - explain why and when to remove.

## Snyk ignore policy

`.snyk` file is allowed ONLY when:
- The vulnerability is provably non-exploitable in your usage (e.g., affects v3() of uuid but you only use v4()).
- The fix would break the application (ESM-only upgrade in CommonJS codebase).
- An expiry date is set (`expires:` field max 90 days).

Always document the justification in detail. Re-evaluate at expiry.

## Deduplication

Multiple versions of the same package bloat bundles and create subtle bugs (instanceof checks fail across copies). Detect:

```bash
pnpm dedupe
pnpm why <package-name>    # find what pulls each version
```

Force dedup via overrides when needed.

## Peer dependencies

Libraries declare `peerDependencies` for shared infra (React, framework, etc) instead of bundling. Apps install them directly.

```json
{
  "peerDependencies": {
    "react": "^18.0.0 || ^19.0.0"
  }
}
```

Use `peerDependenciesMeta.optional: true` for optional integrations.

## Tree-shaking - imports matter

```ts
// BAD - imports the entire library
import _ from 'lodash';
import * as Icons from 'lucide-react';

// GOOD - only the function/icon you use
import debounce from 'lodash/debounce';
import { ChevronRight } from 'lucide-react';
```

For libraries you publish: declare `"sideEffects": false` in `package.json` if accurate; this enables aggressive tree-shaking by consumers.

## Removing unused deps

```bash
pnpm dlx depcheck    # finds deps in package.json that no source file imports
```

Remove ruthlessly. Every dep is attack surface and maintenance load.

## Lockfile discipline

- Commit the lockfile.
- Never edit by hand.
- Resolve merge conflicts by re-running install: delete lockfile, `pnpm install`, commit.
- Use `pnpm install --frozen-lockfile` in CI to detect lockfile drift.

## Workspace deps in monorepo

```json
{
  "dependencies": {
    "@org/shared-types": "workspace:*"
  }
}
```

Use `workspace:*` for in-monorepo packages. Bumping workspace deps is then automatic.

## Ecosystem-specific notes

### React

- Pin React + React-DOM to identical versions.
- Avoid `react@*` in libraries - use `peerDependencies` with semver range.

### TypeScript

- TypeScript itself is `devDependencies`.
- `@types/*` for libs that do not ship types - keep version aligned with the runtime lib.

### Node

- `engines.node` in package.json declares minimum supported version.
- `.nvmrc` / `.node-version` pins development version.

## Renovate / Dependabot

Configure automated PRs:
- Group dev dependencies into a single weekly PR.
- Auto-merge patch updates after CI passes.
- Major updates create individual PRs requiring human review.
- Security updates highest priority - daily.

## Red flags

- Package with single contributor and no commits in 1+ year.
- Postinstall scripts that contact the network.
- License changed mid-life (e.g., Elastic).
- Maintainer transferred to unknown account (supply chain attack vector).
- Sudden 100x size jump between versions.

When you spot one, prefer alternatives or fork.
