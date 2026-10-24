# Publish boundary

Rules for what may leave this machine as a **public** remote versus what must
stay local or private. Complements [LICENSING.md](../LICENSING.md) and
[external-inventory.md](external-inventory.md).

## May be considered for a public remote (after license review)

- Portable forge skills with clear provenance and an acceptable license
- Governance docs: README, CATALOG, PROVENANCE, LICENSING, `references/skill-shape.md`
- Reports that contain no secrets, personal data, or host-specific paths that
  expose private infrastructure

Promotion still requires: catalog status `ready`, license not `unknown` (or an
explicit maintainer waiver recorded in PROVENANCE), and no credential-shaped
files.

## Stay local / private by default

| Item | Reason |
|---|---|
| `pr-creator-tr` / `pr-creator-outcoders` | Team-coupled ADO/Teams/standards |
| `senior-code-reviewer-protocol` STFlow profile | Product/stack-specific gates |
| `air-finance-sentinel` | Operational secrets/host material — never in forge |
| Machine paths, webhook URLs, tenant secrets | Credential or environment binding |
| Personal job-search session data | PII / personal profile |
| Unreviewed `pending-review` skills | License or merge unresolved |

## Pending-review skills

Catalog rows with `pending-review` are usable **locally** via the linker after
conflicts are resolved. They are **not** cleared for public publish until the
checklist in [LICENSING.md](../LICENSING.md) passes.

## Harness linking vs publishing

Linking skills into `~/.cursor/skills` (and siblings) is a **local** operation.
It does not imply the skill is safe to push to a public Git remote.
