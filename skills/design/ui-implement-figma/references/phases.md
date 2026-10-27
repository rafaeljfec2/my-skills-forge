# Phases — progressive, not ceremonial

Work phases 1–12 in order when they apply. **Skip or collapse** a phase with a
one-line reason when it adds no evidence for this request (e.g. no a11y delta,
no perf risk, analysis-only stop after extraction). Do not invent work to fill
the checklist. Prefer claim-scoped evidence over ritual completion.

---

# Phase 1 — Requirements (R)

Understand:

- What screen?
- Which component?
- Is the request visual only?
- Does behavior change?
- Is responsiveness affected?

If architecture changes are required:

STOP.

Open an ADR recommendation.

---

# Phase 2 — Discover

Read before editing.

Discover:

- project instructions
- AGENTS.md
- design tokens
- theme
- typography
- colors
- spacing scale
- reusable components
- neighboring screens
- product specification

Search existing:

- Button
- Card
- Input
- Dialog
- Drawer
- Wizard
- Badge
- Progress
- Tabs
- Timeline
- Layout
- Table
- Skeleton

Prefer extending.

Never duplicate.

---

# Phase 3 — UI Extraction

Separate facts from assumptions.

Output:

## Surface

External container

Header

Body

Footer

Shadow

Radius

Padding

Background

---

## Components

Typography

Spacing

Hierarchy

Icons

Buttons

Inputs

Cards

Tables

Lists

Badges

Charts

---

## Relationships

Grid

Columns

Alignment

Visual rhythm

Whitespace

Reading order

Containment

---

## Responsive

Desktop

Tablet

Mobile

Hidden elements

Fluid elements

---

## Differences

Current implementation

↓

Reference

---

## Proposed scope

Files

Components

Tokens

Reusable patterns

Behavior preserved

---

# Phase 4 — UX Review

Before implementation ask internally:

Can typing be reduced?

Can defaults be inferred?

Can a wizard become simpler?

Can AI prefill something?

Can steps be removed?

Can accessibility improve?

Prefer improving UX instead of copying pixels.

---

# Phase 5 — Design System Validation

Never hardcode:

colors

spacing

radius

typography

shadows

animations

icons

Use project Design Tokens.

If a required token does not exist:

STOP.

Report the missing token.

Do not hardcode.

Every new reusable pattern must strengthen the Design System.

---

# Phase 6 — SDD

Produce a concise Software Design Document.

Include:

Problem

Scope

Components

Files

Dependencies

Responsive behavior

Acceptance criteria

---

# Phase 7 — TDD

Before implementation:

Create

Update

or Extend

tests.

Never remove tests to make code pass.

---

# Phase 8 — Implementation

Implement in order:

1.

Layout

2.

Containers

3.

Typography

4.

Spacing

5.

Components

6.

Interactions

7.

Responsive

8.

Dark Mode

9.

Loading

10.

Empty State

11.

Error State

Never modify business behavior.

Never duplicate state.

Reuse services.

Reuse hooks.

Reuse components.

---

# Phase 9 — Visual Validation

Inspect the rendered UI.

Required viewports:

375x812

768x1024

1440x900

1920x1080

Validate:

Hierarchy

Spacing

Alignment

Containment

Typography

Colors

Radius

Shadows

Responsive behavior

Dark Mode

Do not claim pixel-perfect.

Aim for pixel-close implementation.

UX is more important than exact pixels.

---

# Phase 10 — Accessibility

Validate:

Keyboard navigation

Focus Ring

Contrast

Touch targets

Screen Reader labels

Reduced Motion

Tab order

WCAG AA

---

# Phase 11 — Performance

Avoid:

new dependencies

duplicate CSS

duplicate components

large bundle increases

Prefer:

existing utilities

existing hooks

existing primitives

CSS over JavaScript when possible.

---

# Phase 12 — Quality Gates

Run proportional validation.

Required:

Typecheck

Lint

Tests

Build

Responsive inspection

Dark mode inspection

Existing unrelated failures must be reported separately.

---
