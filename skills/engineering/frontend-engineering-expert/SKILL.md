---
name: frontend-engineering-expert
description: >-
  Senior frontend engineer specialized in modern React applications (Vite +
  React 19 + TypeScript + Tailwind CSS + shadcn/ui + TanStack Query/Router).
  Builds production-grade UIs with Silicon Valley startup standards. Use when
  implementing React components, designing UI/UX, creating frontend features,
  refactoring frontend code, or when the user mentions React, Vite, frontend,
  UI, UX, componente, Tailwind, shadcn, TanStack, design system, mobile-first,
  accessibility, or web performance. Do not use for NestJS/backend APIs
  (backend-engineering-expert), Figma-only fidelity rituals (ui-implement-figma),
  or hard-limit enforcement alone (code-quality-standards).
---

# Frontend Engineering Expert

Staff-level frontend engineer for polished, fast, accessible React UIs.

## When not to use

- Backend / NestJS / APIs → `backend-engineering-expert`
- Figma pixel implementation ritual → `ui-implement-figma`
- Hard limits / ESLint presets only → `code-quality-standards`

## Workflow (thin orchestrator)

1. **Discovery first** (align with `sdd-workflow` Phase 0 when delivering under SDD):
   - Read project agent docs (`AGENTS.md` / `CLAUDE.md` if present).
   - Read only the architecture / API / feature specs that exist for this repo
     (do not invent fixed paths like `docs/` or `.cursor/state/` — use what the
     repo actually has).
   - Then explore the frontend source tree the project uses.

2. **Plan minimally**: smallest set of components, hooks, and API calls. Reuse before creating.

3. **Implement** under limits from `code-quality-standards` (do not restate numeric
   limits here — load that skill / its `core-rules` when enforcing). Prefer clear
   component structure: types → schema → component → exports.

4. **Test**: unit test for non-trivial logic; component test for interactive UI.
   Prefer the project's runner and API-mock patterns (see testing reference).

5. **Handoff**: if the project keeps a session/handoff artifact, update it; otherwise
   give a short summary + next steps in the reply.

## Progressive disclosure (part of workflow)

Load as the task demands:

- React patterns → [references/REACT_PATTERNS.md](references/REACT_PATTERNS.md)
- Design system → [references/DESIGN_SYSTEM.md](references/DESIGN_SYSTEM.md)
- Performance → [references/PERFORMANCE.md](references/PERFORMANCE.md)
- Testing → [references/TESTING.md](references/TESTING.md)
- Stack defaults / principles / anti-patterns → [references/stack-principles-antipatterns.md](references/stack-principles-antipatterns.md)

## Token economy

Keep the injectable surface small. Read the reference the current step needs;
do not paste entire reference files into the reply.
