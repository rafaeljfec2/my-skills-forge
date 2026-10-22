---
name: principal-engineering-workflow
description: >-
  Default engineering workflow for delivery-quality work. After every implementation
  (feature, bugfix, refactor), requires a meticulous self code review, concrete
  correction proposals, applying fixes, and validating with lint/tests/build before
  closing the task. Use whenever implementing code, shipping changes, or when the user
  expects a complete delivery—not only when they explicitly ask for review.
---

# Principal engineering workflow

This skill defines the **mandatory closure** after any implementation. Treat it as the default bar for finished work.

## When to apply

- Whenever you have **changed code** (files created, edited, or removed) in response to a request.
- Before declaring the task **done** or asking the user for a merge or pull request.

## Required flow (after implementation)

### 1. Careful review of your own changes

Review what was delivered as a tech lead:

- **Architecture and boundaries**: cohesion, coupling, and impact on other modules.
- **Correctness and edge cases**: null or undefined, async errors, abort or cancel, and i18n when it applies.
- **Security**: inputs, secrets, injection, data exposure, and the OWASP issues relevant to the stack.
- **Performance and observability**: N+1 queries, payloads, and useful logs without sensitive data.
- **Project standards**: the user's rules (for example `??` versus `||`, no `any`, mobile first on the frontend, `readonly` props, and `Promise.all` only where it makes sense).
- **Tests**: coverage of what changed. Write test descriptions in **English** when you add tests.
- **Lint, types, and formatting**: align with the affected repo's ESLint, Prettier, and `tsc` setup.

### 2. Propose corrections explicitly

- List findings by severity (**critical** / **important** / **minor**).
- For each item, state **what** to change, **where** (files or areas), and **why** (risk or quality).

### 3. Adjust the code

- Apply the corrections that **fit the design**. For large or ambiguous changes, confirm with the user.
- Do not leave an obvious, safe fix as a recommendation only.

### 4. Validate

- Run **lint** and **build** (and tests when they apply) in the **touched** packages. If the monorepo has several projects, state clearly what passed and what failed in the other roots.
- Re-check the IDE **Problems** diagnostics for the changed files.

### 5. Reply to the user

- A short technical summary: what was done, what was corrected after review, and any remaining risks.
- Optional next steps (manual tests, feature flags, docs).
- Write this reply in Brazilian Portuguese unless the user asked for another language.

## Relation to other skills

- For review depth, also follow **[senior-code-review-judge](../../quality/senior-code-review-judge/SKILL.md)** and **[senior-code-reviewer-protocol](../../quality/senior-code-reviewer-protocol/SKILL.md)**.
- For security-specific work, follow **[application-security-expert](../../security/application-security-expert/SKILL.md)** when the flow touches auth, sensitive data, or an attack surface.

## What to avoid

- Do not close an implementation with only "done" and no review or minimal validation.
- Do not change `.env` or secrets without explicit user authorization. The global rule still applies.
