---
name: ui-implement-figma-compact
description: Implements UI from Figma references, screenshots and mockups with high visual fidelity while preserving the project's architecture, Design System, product specifications and business rules. Automatically use when the user provides a UI reference and asks to implement, reproduce, match or apply it.
---

# UI Implement Figma

Implement UI references with evidence-based visual fidelity while preserving architecture, Design System, behavior and data flow.

---

# Core Principles

This project follows mandatory engineering principles.

Every implementation MUST follow:

- SDD (Software Design Document)
- TDD (Test Driven Development)
- RPI (Requirements → Plan → Implementation)

The UI is NEVER the source of truth.

The Product Specification is always the source of truth.

If a Figma reference conflicts with an approved specification:

STOP.

Explain the conflict.

Do not implement.

---

# Authority

Never modify:

- business rules
- domain logic
- API contracts
- DTOs
- pagination
- database models
- matching logic
- backend architecture

Only modify the Presentation Layer unless the user explicitly requests otherwise.

---

# Workflow

Always execute the following phases.

1. Phase 1 — Requirements (R)
2. Phase 2 — Discover
3. Phase 3 — UI Extraction
4. Phase 4 — UX Review
5. Phase 5 — Design System Validation
6. Phase 6 — SDD
7. Phase 7 — TDD
8. Phase 8 — Implementation
9. Phase 9 — Visual Validation
10. Phase 10 — Accessibility
11. Phase 11 — Performance
12. Phase 12 — Quality Gates
