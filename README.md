# my-skills-forge

Local source of truth for agent skills on this machine. Each harness
keeps a real skills directory whose per-skill entries are symlinks into
this checkout. Editing a skill means editing it here.

## Maintainer vs provenance

This repository has a **maintainer** (the owner of the forge). That role
covers curation, naming, domain layout, and validation of the collection.

Maintainer responsibility is separate from authorship of every artifact.
Each skill keeps its own provenance: source path, upstream reference,
authorship notice, and license evidence when available.

See:

- [LICENSING.md](LICENSING.md) — per-artifact licensing policy (no exclusive root license claim)
- [PROVENANCE.md](PROVENANCE.md) — trail for every copied skill
- [CATALOG.md](CATALOG.md) — inventory with status `ready` or `pending-review`
- [references/upstream.lock.md](references/upstream.lock.md) — locked upstream sources
- [references/install-map.md](references/install-map.md) — retired harness names and the forge skills that replace them

## Layout

```
skills/<domain>/<name>/SKILL.md
```

Domains: `engineering`, `architecture`, `quality`, `security`,
`documentation`, `devops`, `design`, `productivity`, `ai-agents`.

Folder name and frontmatter `name` are the same kebab-case English
identifier.

## Consumers

| Harness | Directory | Link |
|---|---|---|
| Cursor | `~/.cursor/skills` (currently `/mnt/c/Users/rafae/.cursor/skills`) | per-skill symlink |
| Claude Code | `~/.claude/skills` | per-skill symlink |
| Codex | `~/.codex/skills` | per-skill symlink, beside `.system` |
| Shared | `~/.agents/skills` | per-skill symlink |

`scripts/link_skills.py` creates those symlinks for every skill under
`skills/`. Both `ready` and `pending-review` skills are installed. The
script leaves an existing real directory in place and reports that name
instead of replacing it. It also leaves harness-owned entries untouched:
`.system` and `air-finance-sentinel`.

Cursor entries are Windows directory symlinks. Their target is the
`\\wsl.localhost\...` path of this checkout, so Windows and WSL read the
same files. Linux harnesses use a direct symlink to the skill directory
in this repository.

```bash
python3 scripts/link_skills.py --dry-run
python3 scripts/link_skills.py
```

## Projects

The linker updates the harness directories above. A project that contains
its own `.cursor/skills/<name>` or `.claude/skills/<name>` still uses
that local copy. Portable skills are the ones linked from the harness.

## Out of this repo / team-coupled

These stay outside `skills/` or are intentionally team-scoped. Do not
copy them into the forge as portable skills:

| Item | Where it lives | Why |
|---|---|---|
| `air-finance-sentinel` | Cursor harness dir | Operational host/user/key material; linker never replaces it |
| Codex `.system` | `~/.codex/skills` | Harness-owned |
| Project-local skills | e.g. game-funny, FlowDeploy-coupled | Point at product files or stack |
| `pr-creator-tr` / `pr-creator-outcoders` | In this forge | Kept, but coupled to TR / Outcoders + ADO config |
| Optional quality-check script | Repo `scripts/` or docs | Prefer repo-local over machine-global paths |
| Vendor / plugin skill caches | Cursor plugins, npm packages | Reinstalled with the tool |

## Status values

- `ready` — copied and usable under the recorded license/provenance
- `pending-review` — present and linked for local use; license or merge review is still open
