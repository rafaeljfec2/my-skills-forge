---
name: ui-implement-figma
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

# Trigger

Automatically use this skill when:

- the user provides a screenshot
- the user provides a Figma reference
- the user provides a mockup
- the user asks to reproduce a UI
- the user asks to make the implementation identical
- the user explicitly invokes ui-implement-figma

An image alone is NOT authorization to modify code.

If the user only wants analysis, stop after the extraction.

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

# Fidelity Checklist

- Outer surface matches
- Internal hierarchy matches
- Typography matches
- Spacing matches
- Grid matches
- Responsive matches
- Dark mode matches
- Design tokens used
- Existing components reused
- No duplicated business logic
- Loading preserved
- Empty preserved
- Error preserved
- Accessibility preserved

---

# Final Report

Respond only with:

## Implemented

Short summary.

## Reused

Components reused.

## New

Components extracted into Design System.

## Validation

Visual inspection

Responsive

Dark mode

Typecheck

Lint

Tests

Build

## Limitations

Only real limitations.

Never narrate tool calls.

Never claim perfection.

State only observable results.
