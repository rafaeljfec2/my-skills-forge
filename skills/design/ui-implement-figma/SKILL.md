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

## Core principles

Every implementation MUST follow SDD, TDD, and RPI (Requirements → Plan → Implementation).

The UI is NEVER the source of truth. The Product Specification is.

If a Figma reference conflicts with an approved specification: STOP, explain, do not implement.

## Trigger

Use when the user provides a screenshot, Figma reference, or mockup and asks to
implement, reproduce, match, or apply it — or explicitly invokes this skill.

An image alone is NOT authorization to modify code. Analysis-only → stop after extraction.

## Authority

Never modify business rules, domain logic, API contracts, DTOs, pagination,
database models, matching logic, or backend architecture unless the user
explicitly requests otherwise. Prefer Presentation Layer only.

## Workflow (thin orchestrator)

Execute phases in order. Load detail only when the phase needs it:

1. Phases 1–12 (Requirements → Discover → Extraction → UX → Design System → SDD → TDD → Implementation → Visual → a11y → Performance → Quality Gates) → [references/phases.md](references/phases.md)
2. Fidelity checklist and final report format → [references/checklist-and-report.md](references/checklist-and-report.md)

## Token economy

Keep the injectable surface small. Read the reference the current phase needs;
do not paste entire reference files into the reply.
