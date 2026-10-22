# Install map

Retired names still present in harness skill directories, and the forge
skill that replaces each one.

`scripts/link_skills.py` creates symlinks under the forge folder name
only. It does not create a symlink with the retired name, and it does
not delete the retired directory. Removing those directories is a later
harness step, after the new names are linked.

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
