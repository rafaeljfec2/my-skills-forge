# Reflect output template

Return a compact report:

```text
Findings
- <workflow>: evidence, frequency/confidence, recommended form.

Recommended changes
- <asset/config/doc>: one-line purpose and why this is the smallest useful form.

Skipped
- <candidate>: why not worth packaging now.

Needs more evidence
- <candidate>: what would make it actionable.
```

If nothing qualifies:

```text
No strong repeated workflow found. I would not add or change any reusable assets yet.
```

## Guardrails

- Do not manufacture assets to justify the workflow
- Do not create overlapping forge skills
- Do not silently change global config, prompts, or permissions
- Do not add broad instructions that make agents more eager, expensive, or invasive without clear benefit
- Do not overfit to a single session unless the user explicitly asks for that exact reusable workflow
- When skill/config files change, tell the user to restart the agent harness if needed
