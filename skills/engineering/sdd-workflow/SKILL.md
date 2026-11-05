---
name: sdd-workflow
description: >-
  Spec-Driven Development workflow: discovery, pipeline phases, evidence path
  and typed green loop, reviewer protocol (Phase 7 MUST spawn
  senior-code-review-judge before PR or done), axioms/limits, and trivial
  fallback. Use when the user asks for SDD, spec-driven delivery, phase gates,
  or reviewer protocol guidance that should stay technology-agnostic.
---

# SDD Workflow

Portable Spec-Driven Development reference pack. The six markdown documents
under `references/` are the source of procedure detail. Constitution = seven
phases + axioms; evidence path and typed green loop sharpen proof; Phase 7
independent review defaults to `senior-code-review-judge`.

## Core contract (non-negotiable)

- Phases 0→7 in order (LIM-02 / AX-01). No phase or Phase 7 step may be skipped.
- **Phase 7 Step 3 is mandatory** before PR, push, merge, or declaring the task
  done.
- Step 3 = a **separate readonly subagent** via Task executing
  **`senior-code-review-judge`** (adapter in `reviewer-protocol.md`). Use
  `senior-code-reviewer-protocol` only when a local rule mandates STFlow.
- **`principal-engineering-workflow` does not replace Step 3.** It may run after
  Phase 6 as author hygiene; it never satisfies AX-05 for SDD delivery.
- Forbidden: reading the judge skill inline in the author context; declaring
  `APPROVED` without a subagent verdict in the session.

## When not to use

- Persisted autonomous execution (state, project commands, resume) → `connexto-development-workflow`. That skill does not replace these phase rules.
- Author closeout after implementation → `principal-engineering-workflow`
  (hygiene only; not Phase 7 Step 3)
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
