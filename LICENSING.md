# Licensing policy

Licensing in this forge is **per artifact**.

## No exclusive root license

There is intentionally **no** root `LICENSE` file that claims exclusive
rights over every imported or derived skill. A single root license would
misrepresent third-party and mixed-provenance content.

## Per-skill rules

1. Preserve `LICENSE.txt`, license headers, and frontmatter fields
   (`license`, `author`, `source`) from the origin.
2. Do not invent permissions. If license evidence is missing, record
   `license: unknown`.
3. Missing metadata does **not** mean the content is free to relicense.
4. Skills with unresolved license questions remain `pending-review` in
   [CATALOG.md](CATALOG.md) until reviewed.
5. README statements in an upstream monorepo (for example "engine is MIT,
   Tech Leads Club skills are CC-BY-4.0 unless noted") are provenance
   evidence for the source repository, not automatic proof for every
   individual `SKILL.md`.

## Attribution

Authorship and license notices must not be stripped during copy,
adaptation, or consolidation. Adaptations are described in
[PROVENANCE.md](PROVENANCE.md).

## Checklist: `pending-review` → `ready`

Do **not** invent a license. Promote only when every box is evidence-backed:

1. **License evidence** — `LICENSE.txt`, SPDX in frontmatter, or upstream notice
   that clearly applies to **this** skill tree (not only a monorepo README claim).
2. **Attribution preserved** — author/source notices still present; PROVENANCE
   delta describes adaptations.
3. **Portability** — skill does not hard-require a single team’s ADO/Teams/tenant
   secrets, or those couplings are documented and accepted as team-coupled
   (then prefer keep `pending-review` or mark not-for-public in CATALOG Notes).
4. **Publish boundary** — reviewed against [references/publish-boundary.md](references/publish-boundary.md).
5. **Catalog update** — set Status to `ready`, set License to the recorded SPDX
   or short name, clear “not for public publish” Notes only when appropriate.

If evidence is missing, leave `pending-review` / `unknown` and keep local-only use.
