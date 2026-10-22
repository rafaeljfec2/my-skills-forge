---
name: sdd-workflow
description: >-
  Spec-Driven Development workflow references: discovery, pipeline phases,
  reviewer protocol, axioms/limits, and trivial fallback. Use when the user
  asks for SDD, spec-driven delivery, phase gates, or reviewer protocol
  guidance that should stay technology-agnostic.
---

# SDD Workflow

Portable Spec-Driven Development reference pack. The five markdown documents
under `references/` are the source of procedure detail.

## When to use

- Starting or resuming an SDD delivery
- Checking phase obligations, reviewer protocol, or trivial-change fallback
- Aligning PR/review language with the SDD axioms and limits

## References

Read in this order unless the user asks for a specific phase:

1. [references/axioms-rules-limits.md](references/axioms-rules-limits.md)
2. [references/phase-0-discovery.md](references/phase-0-discovery.md)
3. [references/pipeline-phases.md](references/pipeline-phases.md)
4. [references/reviewer-protocol.md](references/reviewer-protocol.md)
5. [references/trivial-fallback.md](references/trivial-fallback.md)

## Scope boundary

This skill absorbs only the five reference markdowns from
`sdd-development-protocol-references`. Product-specific `sdd-*.mdc` rule files
and per-app `sdd-protocol.mdc` copies are out of scope and remain in their
source repositories.
