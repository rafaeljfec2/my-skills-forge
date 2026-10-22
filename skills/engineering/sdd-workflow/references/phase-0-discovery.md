# Phase 0 — Project Discovery (Bootstrap, MANDATORY)

> **This phase runs once per session, BEFORE Phase 1**. Without it, the agent will assume conventions that may not match the project, violating AX-08 ("Don't Assume, Verify").

The agent MUST NOT plan, design, or write any code in this project until it has actively discovered:

1. **Project identity & domain** — what this project DOES and WHO it serves
2. **Repository layout** — monorepo? polyrepo? where are apps/packages/services?
3. **Tech stack** — runtime, language, framework, ORM, test runner, package manager
4. **Conventions & rules** — local SDD rule, code style, branch naming, commit format
5. **Essential commands** — how to install, build, test, lint, typecheck, run dev
6. **Available agent skills** — which skills the project ships in `.cursor/skills/` or `.claude/skills/`

## Discovery sequence (in order)

The agent MUST read the following files **in this priority order**, stopping at the first that exists and provides the needed information. If multiple exist, all should be consulted (later files complement earlier ones):

| Order | File / Path                                                                        | Purpose                                                                                                               |
| ----- | ---------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| 1     | `AGENTS.md` (repo root)                                                            | Universal agent briefing — read FIRST. Highest priority.                                                              |
| 2     | `CLAUDE.md` (repo root)                                                            | Claude Code-specific briefing (often complements `AGENTS.md`)                                                         |
| 3     | `.cursor/rules/*.mdc` (local)                                                      | Project-specific Cursor rules (SDD protocol, conventions, design system, etc.) — these OVERRIDE this global baseline  |
| 4     | `README.md` (repo root)                                                            | Project description, stack overview, quick-start commands                                                             |
| 5     | `.claude/skills/`, `.cursor/skills/`                                               | List directory contents to know which skills are available; read `SKILL.md` of any skill relevant to the current task |
| 6     | `CONTRIBUTING.md`, `ARCHITECTURE.md`, `docs/`                                      | Deeper context (architecture diagrams, contribution flow, ADRs)                                                       |
| 7     | `package.json` / `pyproject.toml` / `Cargo.toml` / `go.mod` (root + per-workspace) | Dependencies, scripts, workspace topology                                                                             |
| 8     | `pnpm-workspace.yaml` / `turbo.json` / `nx.json` / `lerna.json`                    | Monorepo topology (which apps/packages exist)                                                                         |
| 9     | `.env.example` (per workspace)                                                     | Required environment variables, expected values                                                                       |
| 10    | Project's CI config (`.github/workflows/`, `.gitlab-ci.yml`, etc.)                 | Quality gates the project actually enforces                                                                           |

## Discovery output (mandatory before Phase 1)

Before responding to the FIRST diff-producing request in a session, the agent MUST internally answer:

- **What is this project?** (1 sentence: domain + purpose)
- **Stack?** (runtime, language, key frameworks, ORM, test runner, package manager)
- **Layout?** (monorepo apps/packages list, or single-app structure)
- **Local SDD rule present?** (yes → it overrides this baseline; no → this baseline applies fully)
- **Test command?** (e.g., `pnpm test`, `pytest`, `cargo test`, `go test ./...`)
- **Lint command?** (e.g., `pnpm lint`, `ruff check`, `golangci-lint run`)
- **Typecheck command?** (e.g., `pnpm tsc --noEmit`, `mypy .`, `cargo check`)
- **Build command?** (e.g., `pnpm build`, `cargo build --release`)
- **Critical-module classification rule?** (if local rule defines one — e.g., HR-21-style criticality)
- **Branch naming convention?** (from local rule or `CONTRIBUTING.md`)
- **Available skills?** (list those that may apply to upcoming work)

If ANY of the items above cannot be determined from existing files, the agent MUST either:

- (a) Run a structural exploration (list root directory, read `package.json`, list workspace folders) BEFORE proceeding, or
- (b) Ask the dev for clarification on the unresolved item

**The agent MUST NEVER assume**: stack, paths, test runner, branch naming, coverage thresholds, criticality definition, or any other project-specific convention. Verify via Phase 0, then act (AX-08).

## When Phase 0 may be skipped

Phase 0 may be skipped (and ONLY skipped) when ALL of these are true:

- The agent has already completed Phase 0 in the current session AND
- The conversation has not switched to a different project / workspace AND
- No local rule files have been created/modified since the last discovery

If in doubt, re-run Phase 0. The cost of a few extra reads is far lower than the cost of an assumption-based bug.

## Phase 0 declaration tag

When the agent runs Phase 0 (typically as part of its first turn in a project), the message MUST be tagged:

```
[Phase 0 — Project Discovery]
```

Subsequent messages may omit Phase 0 tag, but if Phase 0 was skipped erroneously and an assumption is later detected, the agent MUST stop, run Phase 0, and replay from Phase 1.
