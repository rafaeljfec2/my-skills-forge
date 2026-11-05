# AI Memory

The CLI does not call the AI Memory server. It writes `memory/payload.json` when the run enters MEMORY. The orchestrator copies that payload into `memory_write_page` for the workspace and project named in the snapshot, then acks the page path:

```bash
python3 skills/engineering/connexto-development-workflow/scripts/cdw.py memory-payload \
  --repo /path/to/repo --run FEAT-001
python3 skills/engineering/connexto-development-workflow/scripts/cdw.py memory-ack \
  --repo /path/to/repo --run FEAT-001 \
  --role orchestrator --actor orch-1 --page decisions/FEAT-001.md
```

When `memory.enabled` is false, `memory-skip` records the reason and finishes the run. Skipping is refused while memory is enabled. `memory-ack` is refused while memory is disabled.

When `workflow.memory_write_command` and `workflow.memory_read_command` are set, use `memory-sync` instead of `memory-ack`. The engine prepares `memory/body.md`, runs the write backend (stdout JSON with `page_path`, `page_id`, `body_sha256`), reads the page back, verifies the demand id and hash, sets `memory_remote_status` to `confirmed`, then transitions to DONE. Failures leave `pending_sync` and append `memory/sync-log.jsonl`.

The local ack stores the page path only. It does not prove the server accepted the write unless the read-back step succeeded during `memory-sync`.

## Payload fields

- `demand_id`, `demand_type`, `project`, `workspace`, `memory_project`
- `objective`, `risk`
- `decisions` and `failures`
- `commands` with exit codes
- `review`
- `git_branch` and `git_commit` (`null` when no commit was created)
- artifact file names and `run_dir`

Do not paste secrets into the page. The command excerpts are already redacted; still read the page before saving it.

A later reader should be able to reconstruct the demand, the decisions, the commands that ran, and the review outcome without the original chat.
