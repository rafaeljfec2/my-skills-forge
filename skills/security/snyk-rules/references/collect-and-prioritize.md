# Collect and prioritize findings

Read this reference only for workflow step 2.

## Collect

Run the verified Snyk scan for the chosen scope. If the scan fails, is partial, or skips required targets, report that limit. Do not fill the gap with invented results.

For each finding, record only fields the tool returned:

- identifier
- title and description
- scanner and finding type
- reported severity and confidence
- file, line, or dependency
- source or sink excerpt needed to verify it
- package and version, when present
- remediation guidance the tool supplied
- new, pre-existing, or indeterminate
- link the tool supplied

A finding is new only when a baseline scan or the current diff shows it was introduced here. Appearance in this scan alone is indeterminate.

Deduplicate repeated reports of the same issue. Keep distinct paths and attack surfaces as separate rows that share a root-cause id.

Label each row as confirmed, suspected, false-positive candidate, or unresolved. A false-positive candidate still needs evidence. It is not a dismissal.

## Priority

Reported severity is copied from the scanner and never edited. If the scanner omitted severity, write `not reported`. Do not invent a severity.

Remediation priority defaults from that severity:

| Reported severity | Priority |
|---|---|
| critical | P0 |
| high | P1 |
| medium | P2 |
| low | P3 |
| informational, or not reported | P4 |

P0–P4 order the work. They do not replace the scanner severity.

Raise priority by at most one level only when both are evidenced: the finding is new in this change, and a verified path reaches a trust boundary (authentication, authorization, sensitive data, or an exposed entry point). Write the evidence next to the raise.

Do not lower priority. Unclear exploitability stays at the default. Record the uncertainty in one line.

In the reply, name a prioritization factor only when it justified a raise or a shared root cause. Do not walk exploitability, exposure, data sensitivity, reachability, fix safety, regression risk, and novelty for every row.
