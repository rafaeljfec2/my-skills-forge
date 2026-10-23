## Branch Naming Convention

| Prefix | When to use |
|--------|-------------|
| `feat/` | New feature or enhancement |
| `fix/` | Bug fix |
| `chore/` | Dependencies, config, CI changes |

Pattern: `<prefix>AB#<US_NUMBER>-<short-kebab-description>`

Examples:
- `feat/AB#1060986-add-tecnos-fields`
- `fix/AB#1055432-fix-invoice-validation`
- `chore/AB#1070001-update-dependencies`

## Checklist Conventions

For the Code Review Checklist:
- `[x]` = validated and confirmed
- `[ ]` with `(N/A)` = not applicable to this PR
- `[ ]` = not yet validated

## Evidence Images

If the user needs to upload images to the PR body and they aren't embeddable directly, suggest the draft release workaround:

```bash
gh release create pr-<NUMBER>-evidence \
  --title "PR #<NUMBER> - Evidence Images" \
  --notes "Temporary release for PR evidence images." \
  --draft \
  "/path/to/image.png"

gh release view pr-<NUMBER>-evidence --json assets -q '.assets[] | "\(.name) \(.url)"'
```

After the PR is merged:
```bash
gh release delete pr-<NUMBER>-evidence --yes
```
