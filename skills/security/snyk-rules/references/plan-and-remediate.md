# Plan and remediate

Read this reference only in remediate mode, after findings exist. Scan mode does not use this file.

## Plan

Write one plan in Brazilian Portuguese. Group rows that share a safe root-cause fix. Keep each finding id and its own verification.

For each group, include only:

1. Priority and the untouched scanner severity.
2. Finding ids and one explanation.
3. Files, locations, or dependencies.
4. The evidence already collected. Do not restate the whole scan.
5. Impact in one attack scenario.
6. The proposed correction, marked as confirmed, proposed, needs investigation, false-positive candidate, or unsafe to fix now.
7. Files and behavior the change is allowed to touch.
8. Dependency or compatibility risk, if any.
9. The test and the rescan that will accept the fix.

Close with a short summary: scope, capability gaps, counts by severity and priority, new versus pre-existing versus indeterminate, recommended order, shared root causes, and decisions the user must make.

Present the plan and wait. Do not edit code in this step.

If the session cannot pause for approval, do not implement. Report the plan and stop in scan mode.

## Implement

After approval, apply one coherent batch at a time:

1. Read the implementation and the consumers the finding touches.
2. Reproduce the issue when that is feasible.
3. Add a regression test when the repo has a place for it.
4. Apply the smallest fix that stays inside the approved files and behavior.
5. Run the targeted tests and the repo checks that cover that change.
6. Rescan the affected scope with the same verified Snyk capability. The rescan rules are in [verify-and-report.md](verify-and-report.md).

Stop and ask again when the fix needs a business-rule change, a public-contract change, a destructive action, a broad dependency upgrade, a scanner suppression, or any edit outside the approved scope.

Do not add a suppression, ignore, or policy exception without an explicit approval and a written justification. Do not upgrade a dependency without stating compatibility impact. Do not refactor unrelated code. If a finding cannot be fixed safely, say what blocks it and stop that row.
