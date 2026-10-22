# my-skills-forge

Central working collection of reusable agent skills maintained in this
repository.

## Maintainer vs provenance

This repository has a **maintainer** (the owner of the forge). That role
covers curation, naming, domain layout, and validation of the collection.

Maintainer responsibility is **not** the same as authorship of every
artifact. Each skill keeps its own provenance: source path, upstream
reference, authorship notice, and license evidence when available.

See:

- [LICENSING.md](LICENSING.md) — per-artifact licensing policy (no exclusive root license claim)
- [PROVENANCE.md](PROVENANCE.md) — trail for every copied skill
- [CATALOG.md](CATALOG.md) — inventory with status `ready`, `pending-review`, or `held`
- [references/upstream.lock.md](references/upstream.lock.md) — locked upstream sources

## Layout

```
skills/<domain>/<name>/SKILL.md
```

Domains: `engineering`, `architecture`, `quality`, `security`,
`documentation`, `devops`, `design`, `productivity`, `ai-agents`.

Folder name and frontmatter `name` are the same kebab-case English
identifier.

## Status values

- `ready` — copied and usable under the recorded license/provenance
- `pending-review` — present but needs license or merge review
- `held` — cataloged and **not** copied in this migration (portability,
  coupling, secrets, or generated-artifact reasons — not merely "external")
