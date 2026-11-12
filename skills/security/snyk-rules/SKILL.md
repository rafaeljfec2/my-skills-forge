---
name: snyk-rules
description: >-
  Discover the available Snyk integration, scan the requested scope, and report
  findings. Remediate only when explicitly asked, after an approved plan, then
  rescan. Do not use for architectural security review without scanning
  (application-security-expert) or general code-quality gates (code-quality-standards).
---

# Snyk rules

Snyk discovery, scan, and optional authorized remediation.

## When not to use

- OWASP/LGPD/security architecture without tool scan → `application-security-expert`
- General hygiene and size standards without Snyk → `code-quality-standards`

## Workflow (thin orchestrator)

**Scan mode (default):** report only; do not edit code.

1. Discover capabilities and scope → [references/discover-and-scope.md](references/discover-and-scope.md)
2. Collect and prioritize findings → [references/collect-and-prioritize.md](references/collect-and-prioritize.md)
3. Verify and report → [references/verify-and-report.md](references/verify-and-report.md)

**Remediate mode:** only when the user explicitly requests fixes.

1. Reuse steps 1–2 if no current scan exists.
2. Plan, wait for explicit approval, apply fixes within scope → [references/plan-and-remediate.md](references/plan-and-remediate.md)
3. Rescan and report → [references/verify-and-report.md](references/verify-and-report.md)

## Token economy

Read only the reference for the active mode and step. Do not paste long findings into the skill surface; cite tool output and file paths.
