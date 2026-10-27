---
name: ui-implement-figma
description: >-
  Implements UI from Figma references, screenshots and mockups with high visual
  fidelity while preserving architecture, Design System, product specifications
  and business rules. Use when the user provides a UI reference and asks to
  implement, reproduce, match or apply it. Do not use for pure design-system
  theory without an implementation request, or for backend/API work.
---

# UI Implement Figma

Implement UI references with evidence-based visual fidelity while preserving
architecture, Design System, behavior and data flow.

## When not to use

- Backend / API / domain changes → `backend-engineering-expert`
- Architecture trade-offs without UI implementation → `software-architecture-expert`
- General React feature work without a visual reference → `frontend-engineering-expert`

## Core principles

- Prefer SDD / TDD / RPI when the change is a real delivery; **skip or collapse
  phases that do not apply** (evidence over 12-phase ritual).
- The UI reference is NEVER the source of truth — the Product Specification is.
- If Figma conflicts with an approved specification: STOP, explain, do not implement.
- An image alone is NOT authorization to modify code. Analysis-only → stop after extraction.
- Prefer Presentation Layer only; do not change business rules, APIs, DTOs, or
  persistence unless the user explicitly asks.

## Workflow (thin orchestrator)

Execute only the phases that matter for this request. Load detail when needed:

1. Phase detail (Requirements → … → Quality Gates) → [references/phases.md](references/phases.md)
2. Fidelity checklist and report → [references/checklist-and-report.md](references/checklist-and-report.md)

When a phase is irrelevant (e.g. no a11y delta, no perf risk), mark it skipped
with a one-line reason — do not invent work to fill the checklist.

## Token economy

Keep the injectable surface small. Read the reference the current phase needs;
do not paste entire reference files into the reply.
