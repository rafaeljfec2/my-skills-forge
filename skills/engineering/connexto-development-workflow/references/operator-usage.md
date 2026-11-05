# Operator usage (minimal)

This skill is meant to run **inside the target repository** that already has `connexto.project.json`. The human describes the demand; the agent runs `cdw.py` and keeps `.connexto/runs/<id>/state.json` as the checkpoint.

## Install the skill (once per machine)

From **my-skills-forge**:

```bash
pnpm install && pnpm link:apply
```

Restart the agent app (Cursor, OpenCode, VS Code Codex, Claude Code). Confirm:

```bash
ls ~/.cursor/skills/connexto-development-workflow
# or ~/.codex/skills/… or ~/.config/opencode/skills/…
```

## Wire a product repo (once per repo)

1. Add `connexto.project.json` at the repo root ([project-adapter.md](project-adapter.md)).
2. Gitignore `.connexto/`.
3. Align `memory.workspace` / `memory.project` with that repo's `.ai-memory.toml` when memory is enabled.

## What the operator says

Open the **product repo** in the agent (not only the forge).

**New demand** — one message, no CLI required from the human:

```text
Execute with connexto-development-workflow:

Type: FEATURE
Problem: …
Outcome: …
Scope: …
Acceptance: …
```

Optional: `Demand id: FEAT-001`. If omitted, the agent picks the next id.

**Resume** — after a prior run created `.connexto/runs/FEAT-001/`:

```text
Continue FEAT-001 with connexto-development-workflow
```

The agent must call `cdw.py status --repo <root> --run FEAT-001` and follow `next_step`.

## What the agent must do (not the operator)

- Run all `cdw.py` commands; never treat chat history as state.
- On IMPLEMENT with `commands.implement: null`, materialize `developer/task.json`, implement in the repo, submit `developer/report.json` (or `run-developer` when configured).
- On REVIEW, use a different actor and session than the developer; prefer `run-judge` when `workflow.judge_command` is set, otherwise `senior-code-review-judge` readonly + `review` JSON.
- On MEMORY, use `memory-sync` when remote commands are configured; otherwise write AI Memory and `memory-ack` only after a real page write.

## Human approvals only when

- State is `WAITING_APPROVAL` (HIGH risk start, protected actions).
- The agent asks explicitly.

Do not run merge, production deploy, or infrastructure changes through this workflow MVP.

## Maintainer smoke test (forge)

```bash
cd my-skills-forge && pnpm workflow:test && pnpm workflow:proof
```
