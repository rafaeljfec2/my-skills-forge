# Business Rule Guardian — workflow detail

Follow phases in order. Do not skip; do not reorder.

## Phase 1 — Recapture the request (zero dev bias)

Read the original request literally. Ignore any prior interpretation the dev wrote in the PR description. Extract:

1. **The noun**: what resource/feature/flow?
2. **The verb(s)**: what operations (create, block, notify, retry, …)?
3. **The actors**: who triggers it (user, admin, system, external webhook)?
4. **The constraints**: deadlines, thresholds, permissions, data shapes mentioned.
5. **The outcomes**: what the user/system observes on success.
6. **The negatives**: what must NOT happen (leak, charge, duplicate, expose).

If the request is ambiguous, STOP and list the ambiguities. Do not approve around ambiguity.

## Phase 2 — Extract business rules

Translate the request into a numbered list of testable rules. Include both **explicit** (stated) and **implicit** (reasonable PM expectation) rules.

```
BR-01 (explicit): Only admins may start containers on the local host.
BR-02 (implicit): Non-admin attempt must return 403 with an informative message, not 500.
BR-03 (explicit): The action is audit-logged with user, resource, timestamp.
BR-04 (implicit): An audit log write failure must not succeed the action silently.
```

Mark each rule with: **explicit** or **implicit**; a stable ID (`BR-NN`).

## Phase 3 — Map rules → code

For each rule, locate the lines that implement it. Use search/read tools — do not trust PR descriptions.

```
BR-01 → path/to/file.go L87 (RequireAdminForLocal)
BR-02 → path/to/envelope.go L42 — VERIFY the handler returns this, not 500
BR-03 → path/to/audit.go L14 — NOT CALLED ❌
BR-04 → no implementation found ❌
```

## Phase 4 — Edge cases

For every rule, ask at least: empty input; duplicate / already-exists; concurrent calls; downstream failure; partial permission; retry/idempotency; audit / notification / metrics on partial failure.

If the implementation did not cover an edge case a reasonable PM would expect, it is a finding.

## Phase 5 — Scope creep

Anything implemented beyond the stated rules is scope creep and must be justified. Unjustified scope creep → rejection or request a split PR.

## Phase 6 — Complete code review

Audit every dimension below. Findings stand on their own; they need not map to a business rule.

### 6.1 Architecture and layering

Responsibilities in the right layer; no cross-layer leaks; abstraction level consistent; change fits the module's shape.

### 6.2 Patterns and project standards

Follow patterns in the current repository's rules; reuse helpers; idiomatic language; naming conventions.

### 6.3 Code smells

Oversized functions/files; deep nesting; duplication; dead code; narrative comments; magic values; untracked TODOs; god objects.

### 6.4 Error handling

Errors wrapped with context; domain errors at boundaries; no silent swallow; no double-log; no internals leaked to users.

### 6.5 Performance

N+1; unbounded work; blocking I/O on hot paths; missing timeouts; React re-render hotspots when proven expensive; bundle bloat. Flag only when it threatens a real SLO or realistic load.

### 6.6 Security

Auth/authz/session changes always reviewed; validated input; no SQL concatenation / `sh -c` / path traversal; no secrets in logs; CORS/CSRF/rate limits preserved unless justified; privilege escalation guards present; new dependencies checked for supply-chain risk.

### 6.7 Observability

Structured logs with domain fields; no secret/PII in logs/traces/metrics; trace ID where relevant; operator can reconstruct production behavior from logs.

### 6.8 Tests

Every business rule has a behavior assertion (not only `mock.called`); failure paths; no skipped tests without a tracked issue; independent tests; descriptions in English; critical packages covered in the same change when project policy requires it.

### 6.9 Documentation and artifacts

Public APIs, protos, env examples, changelog, ADRs updated when the change warrants it.

### 6.10 Build, lint, versioning

Lint/typecheck clean for touched modules; generated code regenerated; version bumps when project policy requires them for behavior changes.

## Phase 7 — Verdict

| Verdict | Use when |
|---|---|
| **Approved** | All business rules satisfied; no blockers |
| **Approved with conditions** | Business rules OK; non-blocking issues must be tracked |
| **Rejected** | At least one business rule unmet, broken, or bypassed |

Never approve with a question mark. If you have doubts, reject and name them.
