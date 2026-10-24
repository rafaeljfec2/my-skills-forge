# External inventory

Components installed around this forge that are **not** catalog skills under
`skills/`, or that must stay harness-owned. Re-check occasionally — nothing
here auto-updates into the forge.

Last checked: **2026-10-24**.

| Component | Where it lives | Why outside the forge | Update procedure |
|---|---|---|---|
| `air-finance-sentinel` | Cursor harness (`/mnt/c/Users/rafae/.cursor/skills/air-finance-sentinel`; WSL `~/.cursor/skills` → that path) | Operational host/user/key material; linker never replaces it | Maintain in place; never copy into `skills/` |
| Codex `.system` | `~/.codex/skills/.system` | Harness-owned Codex internals | Managed by Codex; leave untouched |
| Retired harness names | e.g. Cursor `buscar-vagas-ti`, `pr-creator-ado`, `senior-code-reviewer` | Old folder names; forge uses new names (see [install-map.md](install-map.md)) | After forge links exist, remove retired dirs manually when safe |
| Claude harness leftovers | `~/.claude/skills/` real dirs (`create-adr`, `create-rfc`, `mermaid-studio`, `senior-code-reviewer`, …) | Pre-forge copies; linker reports `conflict-real` and skips | Diff vs forge; replace with symlink only after backup/delete of real dir |
| Shared agents skills | `~/.agents/skills/ai-memory-*` | ai-memory routing package; not forge catalog | Refresh via ai-memory install / managed skills |
| Codex bundled extras | `~/.codex/skills/` (`imagegen`, `openai-docs`, `plugin-creator` when present) | Ship with Codex / plugins | Update Codex or the owning plugin |
| Project-local skills | e.g. game-funny, FlowDeploy-coupled under a repo `.cursor/skills/` | Point at product files or stack | Keep in the product repo |
| Team-coupled forge skills | `pr-creator-tr`, `pr-creator-outcoders` (in this forge) | ADO/Teams/team standards; not portable publish defaults | Edit in forge; see [publish-boundary.md](publish-boundary.md) |
| Optional quality-check script | Repo `scripts/` or project docs | Prefer repo-local over machine-global paths | Per project |
| Vendor / plugin skill caches | Cursor plugins under `~/.cursor/plugins/`, npm global packages | Reinstalled with the tool | Update the plugin/package; do not vendor blindly into `skills/` |

## Harness path notes (this machine)

| Harness | Skills directory | Notes |
|---|---|---|
| Cursor | `~/.cursor/skills` → `/mnt/c/Users/rafae/.cursor/skills` | Windows dir symlinks via linker |
| Claude Code | `~/.claude/skills` | Several real directories still present (pre-link) |
| Codex | `~/.codex/skills` | `.system` present; few forge links yet |
| Shared | `~/.agents/skills` | ai-memory managed skills only (as of last check) |

## Related docs

- [install-map.md](install-map.md) — retired name → forge skill
- [publish-boundary.md](publish-boundary.md) — public vs local publish rules
- README “Out of this repo / team-coupled” and “Linking harnesses”
