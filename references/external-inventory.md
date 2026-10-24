# External inventory

Components installed around this forge that are **not** catalog skills under
`skills/`, or that must stay harness-owned. Re-check occasionally — nothing
here auto-updates into the forge.

Last checked: **2026-10-24** (catalog skills linked; forge on Windows drive).

| Component | Where it lives | Why outside the forge | Update procedure |
|---|---|---|---|
| `air-finance-sentinel` | Cursor harness (`/mnt/c/Users/rafae/.cursor/skills/air-finance-sentinel`; WSL `~/.cursor/skills` → that path) | Operational host/user/key material; linker never replaces it | Maintain in place; never copy into `skills/` |
| Codex `.system` | `~/.codex/skills/.system` | Harness-owned Codex internals | Managed by Codex; leave untouched |
| Portable skills not in catalog | Cursor/Claude real dirs: `create-adr`, `create-rfc`, `create-technical-design-doc`, `mermaid-studio`, `nestjs-modular-monolith`, `gh-address-comments`, `gh-fix-ci` | Not imported yet; deliberately left as local copies | Import into the forge, then replace with links |
| Shared agents skills | `~/.agents/skills/ai-memory-*` | ai-memory routing package; not forge catalog | Refresh via ai-memory install / managed skills |
| Codex bundled extras | `~/.codex/skills/` (`imagegen`, `openai-docs`, `plugin-creator` when present) | Ship with Codex / plugins | Update Codex or the owning plugin |
| Project-local / product skills | e.g. game-funny, banking-dev, axiom-*, frontend-dev, backend-dev, golang-engineering-expert | Point at product files or stack | Keep in the product repo |
| Team-coupled forge skills | `pr-creator-tr`, `pr-creator-outcoders` (in this forge) | ADO/Teams/team standards; not portable publish defaults | Edit in forge; see [publish-boundary.md](publish-boundary.md) |
| Optional quality-check script | Repo `scripts/` or project docs | Prefer repo-local over machine-global paths | Per project |
| Vendor / plugin skill caches | Cursor plugins under `~/.cursor/plugins/`, npm global packages | Reinstalled with the tool | Update the plugin/package; do not vendor blindly into `skills/` |
| Pre-link backups | `~/skill-backup-2026-10-24/` | Real dirs removed when catalog links were installed | Delete when no longer needed |

## Harness path notes (this machine)

| Harness | Skills directory | Notes |
|---|---|---|
| Cursor | `~/.cursor/skills` → `/mnt/c/Users/rafae/.cursor/skills` | All 22 catalog names are junctions into the forge; leftovers listed above stay as real dirs |
| Claude Code | `~/.claude/skills` | All 22 catalog names are Linux symlinks; portable non-catalog leftovers remain |
| Codex | `~/.codex/skills` | All 22 catalog names are Linux symlinks; `.system` protected |
| Shared | `~/.agents/skills` | All 22 catalog names are Linux symlinks; `ai-memory-*` remain |

## Forge checkout location

| Path | Role |
|---|---|
| `C:\Users\rafae\dev-rafael\my-skills-forge` | Canonical files (Windows drive) |
| `/mnt/c/Users/rafae/dev-rafael/my-skills-forge` | Same checkout from WSL |
| `/home/rafael/dev-rafael/my-skills-forge` | Symlink to the WSL path above |

## Related docs

- [install-map.md](install-map.md) — retired name → forge skill
- [publish-boundary.md](publish-boundary.md) — public vs local publish rules
- README “Out of this repo / team-coupled” and “Linking harnesses”
