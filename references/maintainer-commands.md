# Maintainer commands

The forge uses **pnpm** as the single entrypoint for repository management scripts. Under the hood they call **Python 3.8+** (`scripts/link_skills.py`, `_validate.py`, Connexto `cdw.py`). There are **no npm dependencies**; `pnpm install` only registers the project.

## Prerequisites

| Tool | Purpose |
|---|---|
| Node.js 22+ (or any recent LTS) | Runs pnpm |
| pnpm 11+ | `packageManager` in [package.json](../package.json) |
| Python 3.8+ | Linker, validator, workflow engine |

Enable pnpm once if needed:

```bash
corepack enable
corepack prepare pnpm@11.12.0 --activate
```

## First-time setup

```bash
cd /home/rafael/dev-rafael/my-skills-forge
pnpm install
pnpm link:check
pnpm link:apply
```

Restart Cursor, Codex, OpenCode, or Claude Code after `pnpm link:apply` so skills reload.

## Scripts

| pnpm command | Underlying command | When to run |
|---|---|---|
| `pnpm test` | Connexto (31) + context-budget-guard (32) unit tests | After editing those skills |
| `pnpm validate` | `python3 _validate.py` | Before publishing or after large catalog edits |
| `pnpm link:check` | `link_skills.py --check-repo` | After changing [install-map.md](install-map.md) |
| `pnpm link:dry-run` | `link_skills.py --dry-run` | Before applying links; inspect conflicts |
| `pnpm link:apply` | `link_skills.py` | After adding a skill or fixing a `conflict-real` |
| `pnpm workflow:test` | Connexto unit tests (31 tests) | After editing `connexto-development-workflow` |
| `pnpm workflow:proof` | `cdw.py proof` → `/tmp/connexto-proof` | Smoke test of the workflow engine |

`link:dry-run` and `link:apply` print **SKIP** lines for skills left untouched (`conflict-real`, `conflict-target`). When only those warnings exist, the script exits **0** with `Link status: OK with warnings`. Exit **1** means a real failure (install map, missing harness, or `mklink`/symlink error).

Direct Python invocation remains valid for automation and CI.

## Harness coverage

`pnpm link:apply` installs every skill under `skills/` into:

- Cursor (`~/.cursor/skills`, Windows junctions)
- Claude Code, Codex, shared agents, OpenCode, Antigravity (symlinks)

See [README.md](../README.md) for harness paths and conflict handling.

## Connexto workflow in a product repo

The forge does **not** run demands. A **target repository** needs:

1. `connexto.project.json` (copy from [templates/connexto.project.json](../skills/engineering/connexto-development-workflow/templates/connexto.project.json))
2. `.connexto/` in `.gitignore`
3. The **connexto-development-workflow** skill (via `pnpm link:apply`)

Operators invoke the skill in chat; the agent runs `cdw.py`. See [operator-usage.md](../skills/engineering/connexto-development-workflow/references/operator-usage.md).

Validate a target adapter:

```bash
python3 skills/engineering/connexto-development-workflow/scripts/cdw.py \
  check-config --repo /path/to/target
```

Example product wiring: `connexto-proxy-cli-llms/docs/connexto-workflow.md` when that repo is checked out beside the forge.
