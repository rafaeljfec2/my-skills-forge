# my-skills-forge

Local source of truth for agent skills on this machine. Each harness
keeps a real skills directory whose per-skill entries are links into
this checkout. Editing a skill means editing it here.

Canonical checkout (Windows + WSL):

- Windows: `C:\Users\rafae\dev-rafael\my-skills-forge`
- WSL path: `/mnt/c/Users/rafae/dev-rafael/my-skills-forge`
- Convenience symlink: `/home/rafael/dev-rafael/my-skills-forge` → that checkout

The forge lives on the Windows drive so Cursor can use directory
junctions without UNC `\\wsl.localhost` targets.

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
- [references/skill-shape.md](references/skill-shape.md) — thin-orchestrator contract for every catalog skill
- [references/external-inventory.md](references/external-inventory.md) — harness-owned and vendor components outside the catalog
- [references/publish-boundary.md](references/publish-boundary.md) — what may go public vs stay local
- [references/maintainer-commands.md](references/maintainer-commands.md) — pnpm entrypoint for validate, link, workflow tests

## Prerequisites (maintainer)

| Tool | Notes |
|---|---|
| **pnpm** 11+ | `pnpm install` at forge root; see [references/maintainer-commands.md](references/maintainer-commands.md) |
| **Python** 3.8+ | Linker, `_validate.py`, Connexto `cdw.py` |
| **Node.js** | Runs pnpm (`corepack enable` if needed) |

## Language policy

| Artifact | Language |
|---|---|
| Skills (`skills/**/SKILL.md`, `skills/**/references/**`) | English |
| Repository documentation (README, CATALOG, PROVENANCE, LICENSING, forge `references/*.md`, etc.) | English |
| Generated reports (`reports/**`) | Brazilian Portuguese (PT-BR) |
| Delivery / Cursor plans | Brazilian Portuguese (PT-BR) |
| Chat with the maintainer | Brazilian Portuguese (PT-BR) unless asked otherwise |

Skills and repo docs stay English so harnesses and upstream sharing stay portable.
Reports and plans are operator-facing and follow the maintainer language.

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
| Cursor | `~/.cursor/skills` → `/mnt/c/Users/rafae/.cursor/skills` | per-skill Windows junction (`mklink /J`) into this checkout |
| Claude Code | `~/.claude/skills` | per-skill Linux symlink |
| Codex | `~/.codex/skills` | per-skill Linux symlink, beside `.system` |
| Shared | `~/.agents/skills` | per-skill Linux symlink |
| OpenCode | `~/.config/opencode/skills` | per-skill Linux symlink |
| Antigravity | `~/.gemini/config/skills` | per-skill Linux symlink (global user skills) |
| Antigravity CLI | `~/.gemini/antigravity-cli/skills` | per-skill Linux symlink |

OpenCode also reads `~/.claude/skills` and `~/.agents/skills` for
compatibility, and it resolves a duplicated skill id from the source with
the higher precedence. `~/.config/opencode/skills` is its native source, so
it outranks both compatibility directories.

Antigravity **builtin** trees (`~/.gemini/antigravity/builtin/skills`,
`~/.gemini/antigravity-ide/builtin/skills`) stay package-owned. The linker
never writes there — only into the user skills directories above.

`scripts/link_skills.py` (via **`pnpm link:apply`**) creates those links for every skill under
`skills/`. Both `ready` and `pending-review` skills are installed. The
script leaves an existing real directory in place and reports that name
instead of replacing it. It also leaves harness-owned entries untouched:
`.system` and `air-finance-sentinel`.

Catalog skills must not keep a second real copy under a harness or
project skills directory. Remove the real directory (after backup), then
re-run the linker. Project overrides for catalog names should be
symlinks into this forge, not forks.

### Install / re-link harnesses (step by step)

Editing a skill in this checkout updates every linked harness. Re-run the
linker when you add a catalog skill, after a conflict, or if a link is
missing. Already-correct links do not need reinstall.

1. **Enter the forge**

```bash
cd /home/rafael/dev-rafael/my-skills-forge
# or: cd /mnt/c/Users/rafae/dev-rafael/my-skills-forge
```

2. **Validate the install map**

```bash
pnpm link:check
# or: python3 scripts/link_skills.py --check-repo
```

3. **Preview (no changes)**

```bash
pnpm link:dry-run
```

Inspect `SKIP conflict-real` lines. A harness with a **local copy** of a catalog skill (for example Antigravity `ui-implement-figma`) is skipped on purpose; the run still ends **`Link status: OK with warnings`** and exit code **0**. Exit **1** only on real errors (failed `mklink`, missing map, etc.).

Do not run bare `pnpm link` — that is pnpm's package-link command, not this repo.

4. **Apply links**

```bash
pnpm link:apply
```

Creates Windows junctions for Cursor and Linux symlinks for Claude Code,
Codex, shared agents, and OpenCode — for every skill under `skills/`.

5. **Restart the agent**

Close and reopen the chat (or restart Cursor / Claude Code) so it reloads
`SKILL.md` descriptions. OpenCode re-scans its sources on config changes, so
a new session is enough.

Latest link report: [reports/link-dry-run.md](reports/link-dry-run.md) (PT-BR).

### Maintainer commands (pnpm)

From the forge root, after `pnpm install` (no npm dependencies; scripts only):

| Command | Action |
|---|---|
| `pnpm test` | All Python unit tests (Connexto + context-budget-guard) |
| `pnpm validate` | Run `_validate.py` (catalog, shape, secrets scan) |
| `pnpm link:check` | Validate `references/install-map.md` |
| `pnpm link:dry-run` | Preview harness links |
| `pnpm link:apply` | Apply links to Cursor, Claude, Codex, OpenCode, … |
| `pnpm workflow:test` | Connexto workflow unit tests |
| `pnpm workflow:proof` | End-to-end proof into `/tmp/connexto-proof` |

Requires **Node.js** and **pnpm** on PATH (`corepack enable` if needed).
Python **3.8+** remains required for the underlying scripts.

## Safety

Do not commit credential-shaped files (`.env`, keys, tokens). The validator
scans forge markdown for obvious private-key material and blocks
`air-finance-sentinel` content from landing under `skills/`.

## Projects

Harness links cover every project. A project-local
`.cursor/skills/<name>` or `.claude/skills/<name>` still wins for that
name. For catalog skills, keep those entries as **symlinks into this forge**,
not forks. Product-only skills may stay as real directories in the product
repo.

Optional — replace a project-local real copy with a forge link:

```bash
ln -sfn /mnt/c/Users/rafae/dev-rafael/my-skills-forge/skills/engineering/sdd-workflow \
  /path/to/project/.cursor/skills/sdd-workflow
```

## Out of this repo / team-coupled

These stay outside `skills/` or are intentionally team-scoped. Do not
copy them into the forge as portable skills:

| Item | Where it lives | Why |
|---|---|---|
| `air-finance-sentinel` | Cursor harness dir | Operational host/user/key material; linker never replaces it |
| Codex `.system` | `~/.codex/skills` | Harness-owned |
| Portable skills not yet in the catalog | e.g. `create-adr`, `mermaid-studio`, `gh-fix-ci` | Left in place until imported |
| Project-local / product skills | e.g. game-funny, banking-dev, axiom-* | Point at product files or stack |
| `pr-creator-tr` / `pr-creator-outcoders` | In this forge | Kept, but coupled to TR / Outcoders + ADO config |
| Shared `ai-memory-*` | `~/.agents/skills` | Managed by ai-memory install |
| Vendor / plugin skill caches | Cursor plugins, npm packages | Reinstalled with the tool |

## Connexto development workflow

Recoverable demand loop for a **target repository** (not the forge itself):

`skills/engineering/connexto-development-workflow`

| Audience | Doc |
|---|---|
| Operator (chat only) | [operator-usage.md](skills/engineering/connexto-development-workflow/references/operator-usage.md) |
| Adapter / adoption | [project-adapter.md](skills/engineering/connexto-development-workflow/references/project-adapter.md) |
| Example product | `connexto-proxy-cli-llms/docs/connexto-workflow.md` |

Install the skill with **`pnpm link:apply`**, add `connexto.project.json` on the product repo, then invoke the skill in chat (see operator doc).

Forge smoke tests: **`pnpm workflow:test`**, **`pnpm workflow:proof`**.

SDD phase rules, author self-review, and independent review stay in
`sdd-workflow`, `principal-engineering-workflow`, and `senior-code-review-judge`.

## Status values

- `ready` — copied and usable under the recorded license/provenance
- `pending-review` — present and linked for local use; license or merge review is still open
