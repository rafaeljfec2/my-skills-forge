# Verify and report

Read this reference for the scan-mode report, and again after an approved remediation batch.

## Rescan after a fix

1. Confirm the approved edit is present.
2. Run the regression test and the project checks for that change.
3. Rescan the same scope with the verified Snyk tool.
4. Match new results to the original finding ids.
5. Mark each targeted id resolved or still present.
6. Record findings that appeared after the edit.
7. Continue only inside the approved scope.

If the rescan fails or the tool is gone, status is `FIXED_NOT_VERIFIED` or `BLOCKED`. Do not claim a clean result.

A passing rescan covers that scope only. It does not mean the application is secure.

Stop when every authorized actionable id is verified, when the rest need a user decision or an external change, when permission or tooling blocks progress, or when the next edit would leave the approved scope.

## Status values

Use one status per finding id:

- `FIXED_AND_VERIFIED` — the fix is in the tree and the rescan no longer reports that id.
- `FIXED_NOT_VERIFIED` — the fix is in the tree and the rescan did not run or did not cover it.
- `UNRESOLVED` — still reported, or not attempted.
- `FALSE_POSITIVE_CANDIDATE` — evidence suggests it does not apply. Scanner severity stays. This is not a suppression.
- `BLOCKED` — a safety, permission, or tooling limit stopped the work.

## Report

The report is Brazilian Portuguese and short.

Scan mode, and any run that did not edit code: scope, which capabilities were usable, counts by severity and priority, each id with location and one-line impact, new versus indeterminate, and coverage gaps. No fix proposal unless the user asked for a plan.

After remediation, do not repeat the plan. For each id report status, the check or rescan that supports it, and what remains. Then list tests and scans run, findings introduced by the fix, tool failures, and decisions still open.

Do not paste the raw scan. Do not claim success past the evidence.
