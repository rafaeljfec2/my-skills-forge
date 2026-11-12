# Refactoring and design hygiene (authoring)

Read this reference when creating or refactoring code in step 1 of the principal workflow.

## SOLID (only with evidence in touched code)

- **SRP:** one responsibility per module; split when reasons to change diverge.
- **OCP:** extend via new types or hooks without editing the stable branch.
- **LSP:** subtypes honor the caller contract (no surprising errors or weakening).
- **ISP:** narrow interfaces; no methods the client never uses.
- **DIP:** depend on abstractions at unstable boundaries (ports), not concrete adapters.

Do not add interfaces, base classes, or patterns without a **second real use** in the codebase or an explicit upcoming caller.

## DRY and Rule of Three

1. First occurrence: make it work.
2. Second duplicate: tolerate it; record the discomfort.
3. Third duplicate: extract a shared function/module.

Do not abstract on the second copy.

## Two hats

In one cycle, either **add behavior** without reshaping unrelated structure, or **restructure** without changing behavior. Prep refactors finish and are verified before the new feature lands on top.

## When to restructure

| Kind | When |
|---|---|
| Preparatory | Before the feature needs the new shape |
| Comprehension | While reading (rename, extract small helpers) |
| Garbage collection | Small dead code on the path; ticket the rest |
| Planned | Quality debt blocks the change |

## Test safety net

Structural refactors require running the project's test command in the same cycle. If no tests cover the touched behavior, say so; do not call the change a safe refactor.

## Short steps

Edit → compile/test → continue. If something breaks, the step was too large — revert and slice smaller.

## Smells → techniques

| Smell | Technique |
|---|---|
| Duplication (third copy) | Extract Function / Module |
| Long function | Extract Method |
| Large class / file | Extract Class; respect file-size bands in review `scans.md` |
| Long parameter list | Introduce Parameter Object |
| Switch on behavior kind | Replace Conditional with Polymorphism (only when pain is real) |
| Unclear name | Rename until intent is obvious |
