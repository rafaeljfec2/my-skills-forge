# Install map

Retired names still present in harness skill directories, and the forge
skill that replaces each one.

`scripts/link_skills.py` creates links under the forge folder name only.
It does not create a link with the retired name, and it does not delete
the retired directory. On this machine the retired harness directories
listed below were removed on 2026-10-24 after the catalog links were
installed (backups under `~/skill-backup-2026-10-24/`).

`air-finance-sentinel` stays in the Cursor skills directory. The linker
does not replace it.

## Replacements

| Retired harness name | Forge skill |
|---|---|
| buscar-vagas-ti | skills/productivity/job-search |
| pr-creator-ado | skills/devops/pr-creator-tr |
| senior-code-reviewer | skills/quality/senior-code-review-judge |
| senior-code-reviewer | skills/quality/senior-code-reviewer-protocol |

`senior-code-reviewer` maps to two skills. Both stay in the forge.
`pr-creator-outcoders` is a separate forge skill and is linked under
its own name.
