# Project adapter and adoption

Another repository does not copy this framework. It adds one config file and invokes this skill from the forge. Harness links point at the forge after `pnpm link:apply` in **my-skills-forge** (or `python3 scripts/link_skills.py`).

The schema is JSON, read by the Python standard library. YAML is not accepted.

For **operator-only** instructions (chat prompts, no CLI), see [operator-usage.md](operator-usage.md).

## File

Path: `<target-repo>/connexto.project.json`

```json
{
  "project": {"name": "example-project", "language": null, "framework": null},
  "commands": {
    "install": null,
    "test": "python3 -m unittest",
    "lint": null,
    "typecheck": null,
    "build": null,
    "implement": null
  },
  "quality": {
    "require_tests": true,
    "require_lint": false,
    "require_typecheck": false,
    "require_build": false,
    "max_validate_attempts": 3,
    "command_timeout_seconds": 120
  },
  "git": {"base_branch": "main", "isolated_branch": true, "allow_commit": false},
  "memory": {"enabled": true, "workspace": "default", "project": "example-project"},
  "workflow": {
    "max_review_rounds": 3,
    "developer_command": null,
    "judge_command": null,
    "memory_write_command": null,
    "memory_read_command": null
  }
}
```

Template: [templates/connexto.project.json](../templates/connexto.project.json).

`language` and `framework` may be null. They are never defaulted. Every top-level key is required. Command keys may be null. A required quality gate needs a non-empty command. At least one gate must be required. Unknown keys are errors.

```bash
python3 skills/engineering/connexto-development-workflow/scripts/cdw.py check-config --repo <target>
```

### `commands.implement`

When **null** (default for agent delivery), the developer edits the tree and submits `developer/report.json` (see [roles.md](roles.md)). When set, `implement-hook` runs that argv once.

### `workflow` (v0.2)

| Key | Purpose |
|---|---|
| `max_review_rounds` | Cap REVIEW → IMPLEMENT loops |
| `developer_command` | Optional subprocess; env `CDW_DEVELOPER_*` |
| `judge_command` | Optional subprocess; bundle under `review/judge-input/` |
| `memory_write_command` / `memory_read_command` | Pair required together; use `memory-sync` instead of local-only ack |

Reference backends for tests live under `scripts/backends/`; production should point at your agent runtime and AI Memory tooling.

## Adopt

1. Add `connexto.project.json` with commands that already exist in that repository.
2. Ignore `.connexto/` in git.
3. From **my-skills-forge**, run `pnpm link:apply` so **connexto-development-workflow** is on the harness.
4. Open the target repo in the agent and start a demand via [operator-usage.md](operator-usage.md), **or** run `cdw.py init` manually:

```bash
python3 /path/to/my-skills-forge/skills/engineering/connexto-development-workflow/scripts/cdw.py init \
  --repo /path/to/target \
  --demand-id FEAT-001 \
  --type FEATURE \
  --problem "..." \
  --outcome "..." \
  --scope "..." \
  --project example-project \
  --criterion "..."
```

5. Follow [lifecycle.md](lifecycle.md). Stop only after `state.json` is saved.
6. On the next session, `status` and continue from `next_step`, or ask to continue the demand id in chat.
7. SDD phase rules, author hygiene, and independent review stay in their own skills.
8. Memory: see [memory.md](memory.md) — remote confirmation requires read-back when sync commands are configured.

Demand ids: `FEAT-001`, `BUG-001`, `REFACTOR-001`, `HOTFIX-001`, `DEBT-001`. Brief `target_project` must equal `project.name`.

## Example: connexto-proxy-cli-llms

- `project.name`: `connexto-proxy-cli-llms` (matches `.ai-memory.toml`)
- Validation: `pnpm test`, `pnpm lint`, `pnpm typecheck`
- Doc: `docs/connexto-workflow.md` in that repository
