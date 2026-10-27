---
name: sdd-workflow
description: >-
  Spec-Driven Development workflow: discovery, pipeline phases, evidence path
  and typed green loop, reviewer protocol (Phase 7 via senior-code-review-judge),
  axioms/limits, and trivial fallback. Use when the user asks for SDD,
  spec-driven delivery, phase gates, or reviewer protocol guidance that should
  stay technology-agnostic.
---

# SDD Workflow

Portable Spec-Driven Development reference pack. The six markdown documents
under `references/` are the source of procedure detail. Constitution = seven
phases + axioms; evidence path and typed green loop sharpen proof; Phase 7
independent review defaults to `senior-code-review-judge`.

## When not to use

- Author closeout after implementation → `principal-engineering-workflow`
- Standalone evidence-first PR review **outside** an SDD delivery →
  `senior-code-review-judge` (inside SDD, Phase 7 **uses** that skill via the
  reviewer adapter)

## When to use

- Starting or resuming an SDD delivery
- Checking phase obligations, evidence path, reviewer protocol, or trivial-change fallback
- Aligning PR/review language with the SDD axioms and limits

## Workflow (thin orchestrator)

Read only the phase/document needed:

1. [references/axioms-rules-limits.md](references/axioms-rules-limits.md)
2. [references/phase-0-discovery.md](references/phase-0-discovery.md)
3. [references/pipeline-phases.md](references/pipeline-phases.md)
4. [references/evidence-and-loop.md](references/evidence-and-loop.md)
5. [references/reviewer-protocol.md](references/reviewer-protocol.md)
6. [references/trivial-fallback.md](references/trivial-fallback.md)

## Scope boundary

This skill owns the SDD reference pack plus forge-owned `evidence-and-loop.md`.
Product-specific `sdd-*.mdc` rule files and per-app `sdd-protocol.mdc` copies
are out of scope (local rules override this baseline).

## Token economy

Keep the injectable surface small. Read the reference the current phase needs;
do not paste entire reference files into the reply.
