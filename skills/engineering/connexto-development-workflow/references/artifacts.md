# Artifacts

Each demand uses one directory:

```text
<target-repo>/.connexto/runs/<demand-id>/
  brief.md
  research.md
  spec.md
  plan.md
  tasks.md
  validation.md
  review.md
  review.json
  delivery.md
  project.snapshot.json
  state.json
  memory/payload.json
  evidence/execution.jsonl
  evidence/commands.jsonl
```

Add `.connexto/` to the target repository `.gitignore`. The snapshot is the config used for the whole run. Later edits to `connexto.project.json` do not change an open run.

Hand-written files are `research.md`, `spec.md`, `plan.md`, and `tasks.md`. The engine writes the others.

| File | Required content |
|---|---|
| `brief.md` | demand id, problem, desired outcome, success criteria |
| `research.md` | `## Facts`, `## Hypotheses`, `## Gaps`, `## Evidence`, and the line `Implemented: no` |
| `spec.md` | `## Behavior` |
| `plan.md` | `## Acceptance criteria` |
| `tasks.md` | at least one `- [ ]` task |
| `review.json` | summary, findings with severity, file, location, and rationale |
| `delivery.md` | problem, solution, files, validation, review, git, limitations, follow-ups, release actions |

Templates in `templates/` match these headings. Copy them into the run with `cdw.py put` only for the hand-written files.

Command evidence stores argv, exit code, timeout flag, timestamps, and redacted excerpts. It does not store the process environment.
