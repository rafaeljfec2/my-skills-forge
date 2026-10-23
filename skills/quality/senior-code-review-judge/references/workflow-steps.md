# Judge workflow steps (detail)

Load this file when executing a review. The `SKILL.md` holds mission and principles only.

## Step 0 — Mode, scope, and project profile

Identify the mode:

- **LOCAL**: repository checkout is available.
- **REMOTE**: only a PR URL or remote diff is available.
- **PATCH-ONLY**: only pasted diff or changed snippets are available.

Identify the change profile: **CODE**, **DOCS-ONLY**, **CONFIG / INFRA**, or **MIXED**.

Do not infer DOCS-ONLY from extensions alone. Inspect the role and content of changed files. Scripts, CI workflows, JSON/YAML configuration, permissions, and deployment manifests may change runtime or security behavior.

Detect stack/project profile from manifests, repository instructions, and nearby code. Apply any named project profile only when its detection conditions are met. For example, STFlow-specific rules apply only when both `apps/api/drizzle.config.ts` and `pnpm-workspace.yaml` with `apps/*` are present. See [scans.md](scans.md) for profile-specific searches.

Record:

- base and head revisions, if available;
- changed files and diff size;
- intent: feature, bugfix, refactor, guardrail, config, docs, or mixed;
- affected workspaces/modules;
- risk level: LOW, MEDIUM, HIGH, or CRITICAL, with one-sentence justification;
- limitations of the available context.

If the target is a PR and tools are available, inspect its title, description, author, base/head, changed files, and diff. For local work, resolve the base branch using repository instructions and Git state; do not assume `main` or `origin/HEAD` without checking.

## Step 1 — Deterministic verification

Discover existing project commands from repository instructions and the actual manifests/CI configuration. Prefer the project's own commands over guessed commands.

Run relevant available checks, usually: lint; typecheck; focused tests for changed behavior; broader tests when risk and cost justify them; build; existing security/dependency/IaC/SAST scanners relevant to the change; project-specific budgets or architectural checks, if configured.

For each check, record `PASS`, `FAIL`, `NOT RUN`, or `NOT AVAILABLE`, plus the command and concise observed result. Never report `PASS` for a command that did not complete successfully.

If a check fails:

1. Determine whether the failure is caused by the patch, pre-existing, environmental, or unclear.
2. Compare with the base branch or known baseline when feasible.
3. Report a patch-caused failure as a blocking correctness/build issue when it prevents the intended change from working.
4. Do not label every lint/test/build failure as the same category or automatically assume every failure was introduced by the patch.
5. If attribution cannot be established, report `BASELINE/ATTRIBUTION UNCLEAR` and lower review confidence.

For DOCS-ONLY changes, skip irrelevant application checks, but validate links, examples, scripts, configuration semantics, and generated artifacts when applicable.

Do not install new tooling merely to conduct the review. Use existing tools and explain meaningful gaps.

## Step 2 — Scope and change understanding

Read every changed source file in full when practical; never rely on memory or only on a patch excerpt for a local review. For remote/patch-only mode, clearly state that unchanged code may be unavailable.

Summarize the intended behavior in one sentence. Identify:

- contracts and invariants the change must preserve;
- callers/callees and equivalent execution paths;
- persistence/schema/API boundaries;
- new dependencies or version changes;
- failure, retry, timeout, and rollback behavior;
- tests expected to demonstrate the change.

Classify files as core or mechanical (generated code, lockfiles, snapshots, vendored dependencies, build artifacts). Mechanical files may be excluded from line-by-line semantic review when their source of truth is checked, but list exclusions and inspect them if the change itself suggests tampering or a meaningful behavior change.

Detect moved code. Do not report copied/moved unchanged lines as newly introduced defects unless the move changes behavior or context.

## Step 3 — Risk-based review passes

Review changed core code using the relevant passes below. Do not force irrelevant passes onto every change. Also consult [rigorous-checks.md](rigorous-checks.md) and [blind-spots.md](blind-spots.md).

### Pass A — Correctness and intent

- Does the implementation satisfy the stated intent and acceptance criteria?
- Are invariants preserved across success, failure, retry, and partial completion?
- Are edge cases handled, including empty/null/zero values where meaningful?
- Are errors swallowed, misreported, or converted into success?
- Are state transitions valid and idempotent where needed?
- Do changes introduce races, deadlocks, duplicate processing, lost updates, or ordering assumptions?
- Does the PR description claim a fix or result that tests, reproduction, or measurements do not support?

### Pass B — Entry-point and guard tracing

For each new or modified guard, validation, permission check, tenant filter, or business rule:

1. State what operation or invariant it protects.
2. Identify all relevant paths that can perform that operation: HTTP controllers, services, workers, scheduled jobs, event handlers, CLI commands, GraphQL/resolvers, webhooks, and direct database writes as applicable.
3. Trace each path far enough to find central or upstream protections.
4. Verify whether the protection applies on each path and under the relevant trust boundary.
5. Report a bypass as a defect only when the path is reachable and the missing protection creates a concrete risk or incorrect behavior.

Use this output when useful:

`ENTRY POINT TRACE: <invariant>`

- `path A -> GUARDED (evidence)`
- `path B -> GUARDED BY <central layer> (evidence)`
- `path C -> GAP (evidence and impact)`

An unguarded-looking path is a candidate, not automatically a critical vulnerability. Classify based on demonstrated reachability, trust boundary, impact, and available evidence.

### Pass C — Test adequacy

For each new or changed behavior:

- Locate tests and identify what behavior they execute.
- Check whether mocks, stubs, DI overrides, fixtures, or test doubles allow the new logic to run.
- Verify assertions for success, negative, error, and fallback paths proportionate to risk.
- Check that assertions prove outcomes rather than merely asserting a mock was called.
- Check whether existing tests were weakened, skipped, deleted, or made less meaningful.
- When feasible, test the new regression test against the base implementation. If it passes unchanged on the base, it may not prove the regression was fixed.
- Do not modify the test suite during review.

Zero tests is not automatically a critical defect for every change. Treat missing tests as blocking when risk, project policy, or the nature of the behavior makes them necessary—especially security, money, data integrity, concurrency, migrations, and critical business rules. Otherwise report a proportionate gap or explain existing alternative evidence.

### Pass D — Security and data integrity

Check applicable risks: authentication, authorization, IDOR/BOLA, tenant isolation; SQL/command/template injection and unsafe deserialization; secret exposure, sensitive data in logs, PII handling; unsafe redirects, path traversal, SSRF, trust-boundary violations; cryptographic/TLS bypasses and insecure defaults; mass assignment and validation gaps; privilege escalation and insecure webhook handling; transaction boundaries, data loss, unsafe retries, duplicate side effects; migration safety, constraints, indexes, rollback, and cross-tenant effects; dependency vulnerabilities when supported by current scanner/advisory evidence.

For multi-tenant queries, verify the actual data-access path and protections. Profile-specific STFlow checks (when detected) are in [scans.md](scans.md). Do not apply those rules to unrelated repositories.

Security findings should be high-confidence and tied to a plausible threat path. Avoid claiming exploitability based solely on a keyword or suspicious-looking API.

### Pass E — Structure, maintainability, and performance

- Is there duplicated logic that risks behavioral divergence?
- Are responsibilities and module boundaries clear?
- Is a new abstraction justified by actual reuse or domain meaning?
- Is complexity growing in a way that makes defects likely?
- Are there N+1 queries, avoidable I/O in hot paths, unbounded work, or missing pagination?
- Are resource limits, timeouts, retries, and cancellation appropriate?
- Are types and defaults correct for the language and project conventions?
- Are comments useful, accurate, and non-obvious?
- Is the change consistent with the established architecture and design system?

Use file-size and complexity thresholds as signals, not universal proof of a defect. For TypeScript, check `any`, unsafe casts, missing public API return types, `||` versus `??`, and conditional rendering only when they create a demonstrated risk or violate a documented project rule.

### Pass F — Bypasses, duplication, and workaround patterns

Inspect relevant changes for: suppression directives without adequate justification; skipped/disabled tests or weakened assertions; swallowed exceptions; unsafe casts or type-check bypasses; TLS/security-check bypasses; sleep-based synchronization; unexplained magic values; duplicated code that can drift; commented-out code and comments that merely restate implementation; workarounds that hide the root cause.

Use deterministic scanners already present in the project when possible. Scanner hits are candidates, not findings: inspect context and justification before reporting.

## Step 4 — External research and evidence

If a candidate finding depends on external behavior (framework/API semantics, dependency versions, deprecations, security advisories, or version-specific language behavior), consult current official documentation, release notes, or security advisories.

- Prefer official sources.
- Record the exact URL and the claim it supports or refutes.
- Do not use memory as the sole basis for version-sensitive claims.
- If research is unavailable, state that limitation and phrase the point as a question or omit it if unsupported.
- If the diff touches no external surfaces, record `No external surfaces requiring research`.

For every candidate finding, gather: exact file and line; minimal code excerpt; expected versus actual behavior; concrete impact and conditions required; relevant test/tool output, official source, or safe local reproduction when available; confidence: HIGH, MEDIUM, or LOW.

Reproduce suspected critical defects when practical and safe, inside the repository's test harness or isolated local environment. Never perform network attacks or destructive tests. If a feasible reproduction contradicts the claim, remove or revise the finding.

## Step 5 — Verify, challenge, and deduplicate findings

Before reporting each candidate:

1. Re-open the cited code and confirm the line.
2. Check surrounding logic, direct callers/callees, tests, and centralized protections as needed.
3. Ask: what evidence would prove this suspicion wrong?
4. Search for that counter-evidence.
5. Verify the issue is introduced by this change. Pre-existing issues must not be presented as regressions; mention them separately only if materially relevant and clearly labeled.
6. Check whether deterministic tooling already reports it.
7. Deduplicate findings and prefer one actionable finding over multiple comments on the same root cause.
8. Assign severity based on demonstrated impact, not on the suspicious pattern alone.
9. Provide a concise fix direction, not a full implementation unless requested.

If a claim cannot be grounded, do not present it as a confirmed defect. Depending on usefulness, omit it or report an explicitly labeled uncertainty/question.

## Step 6 — Severity and verdict

Severities:

- **CRITICAL-SECURITY**: demonstrated or strongly evidenced exploitable security flaw, broken authorization/tenant isolation, serious sensitive-data exposure, or comparable high-impact security risk. Blocks merge and escalates.
- **CRITICAL-CORRECTNESS**: demonstrated data loss/corruption, incorrect money, broken critical business invariant, unsafe irreversible migration, severe concurrency defect, or a failure that makes the change unusable. Blocks merge.
- **IMPORTANT**: confirmed material defect or regression that should be fixed before merge, but does not meet critical criteria.
- **MINOR**: low-impact issue, maintainability concern, or non-blocking improvement supported by evidence.
- **OBSERVATION**: useful context or risk that is not a confirmed defect; keep concise and do not inflate severity.
- **PRE-EXISTING**: materially relevant issue not introduced by this patch. Clearly label it and do not use it alone to reject the change.

Verdicts:

- **REJECTED**: at least one CRITICAL finding, or a patch-caused verification failure that blocks intended use.
- **APPROVED_WITH_NOTES**: no critical findings, but one or more IMPORTANT/MINOR issues or material limitations remain.
- **APPROVED**: no critical or important findings and relevant verification is sufficient for the risk level.
- **INCOMPLETE**: critical verification could not be performed or required context is missing, so a defensible approval is not possible. State what is missing and how to resolve it.

Do not reject solely because: any check failed without establishing patch attribution or relevance; a behavior lacks a test regardless of risk; a path lacks a local guard before checking other layers; a style heuristic was triggered without a concrete defect; an issue is uncertain or merely pre-existing.

If a project has stricter documented merge policies, honor them and explain how they affect the verdict.

## Step 7 — Re-review and convergence

When reviewing a later round:

1. Retrieve the prior review and finding IDs/ledger if available.
2. Verify each previous finding against the new commits: `RESOLVED`, `OPEN`, or `DECLINED` with evidence and rationale.
3. Re-run relevant checks.
4. Inspect the new diff for regressions introduced by the fixes.
5. Do not intentionally hold findings from round one to create another round.
6. New findings are allowed when genuinely discovered; prioritize material defects.
7. Avoid reopening an accepted disagreement without new evidence.
8. If the review cannot be completed due to missing access or tools, mark `INCOMPLETE` instead of implying approval.

Keep each round focused on unresolved findings and regressions introduced by the latest changes.

## Step 8 — Report format

Use the template in [report-template.md](report-template.md). Return one consolidated report in the user's requested language (conversation language if unspecified). Keep code identifiers and tool output verbatim.

## Step 9 — Publishing external reviews

Publishing is an external side effect. Follow [publishing.md](publishing.md).

- If the user explicitly asked to review a PR and authorized publishing, publish one consolidated review.
- If authorization is unclear, provide the review in chat and ask before publishing.
- Never claim a review was posted unless the tool confirms success.
- Do not open PRs, merge branches, or modify code as part of this skill unless separately requested.

## Optional project-specific rules

Project-specific rules belong in a clearly labeled profile/reference file and are applied only when profile detection succeeds. Keep generic principles stack-agnostic. For STFlow when detected, use the STFlow sections in [scans.md](scans.md). These are review prompts, not automatic findings.

## End-of-review quality gate

Before returning the report, confirm:

- [ ] Every finding is introduced by the patch or labeled PRE-EXISTING.
- [ ] Every finding has a verified location and concrete evidence.
- [ ] Suspicious patterns were traced to behavior and impact.
- [ ] Centralized/alternative protections were checked where relevant.
- [ ] Tool results distinguish PASS, FAIL, NOT RUN, and NOT AVAILABLE.
- [ ] Missing tests are judged by risk and project policy.
- [ ] External claims are backed by current official sources or explicitly qualified.
- [ ] Findings are deduplicated and severity is proportional.
- [ ] The verdict follows the stated rules.
- [ ] Review limitations are visible; INCOMPLETE is used when necessary.
- [ ] No code was changed and no external review was published without authorization.
