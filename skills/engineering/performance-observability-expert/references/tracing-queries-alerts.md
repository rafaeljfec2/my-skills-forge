# Distributed Tracing + Query Optimization + Alerting

## Distributed Tracing

### Concepts

- **Trace**: complete request flow across services
- **Span**: individual operation within a trace
- **Context Propagation**: passing trace context between services

### OpenTelemetry Implementation

```typescript
import { trace, SpanStatusCode } from "@opentelemetry/api";

const tracer = trace.getTracer("user-service");

async function createUser(data: CreateUserDto) {
  const span = tracer.startSpan("createUser");
  try {
    span.setAttributes({
      "user.email": data.email,
      "operation.type": "create",
    });
    const user = await repository.save(data);
    span.setStatus({ code: SpanStatusCode.OK });
    span.end();
    return user;
  } catch (error) {
    span.setStatus({ code: SpanStatusCode.ERROR, message: error.message });
    span.recordException(error);
    span.end();
    throw error;
  }
}
```

### Context Propagation

```typescript
import { context, propagation } from "@opentelemetry/api";

const incomingContext = propagation.extract(context.active(), headers);

const outgoingHeaders = {};
propagation.inject(context.active(), outgoingHeaders);
```

### Trace Structure

```
Trace (Request ID: abc123)
├── Span: HTTP GET /users
│   ├── Span: Database Query (findUsers)
│   │   └── Span: Index Lookup
│   └── Span: Serialize Response
└── Span: HTTP Response
```

## Query Optimization

### Identify Slow Queries

- Enable slow query log
- Use query profiling
- Monitor execution time
- Analyze query plans (`EXPLAIN ANALYZE`)

### Techniques

- Add indexes on frequently queried columns
- Use appropriate index types (B-tree, hash)
- Avoid N+1 (use joins, eager loading)
- Use query result caching
- Optimize JOIN operations
- Use materialized views for complex queries

### Example: N+1 → Single Query

```typescript
// Bad: N+1
const users = await userRepository.find();
for (const user of users) {
  const profile = await profileRepository.findOne({ userId: user.id });
}

// Good: single query with join
const users = await userRepository.find({ relations: ["profile"] });

// Good: query builder
const users = await userRepository
  .createQueryBuilder("user")
  .leftJoinAndSelect("user.profile", "profile")
  .getMany();
```

### Index Strategy

```sql
CREATE INDEX idx_users_email ON users(email);

CREATE INDEX idx_orders_user_date ON orders(user_id, created_at);

EXPLAIN ANALYZE SELECT * FROM users WHERE email = 'user@example.com';
```

## Alerting

### Design Principles

- **Actionable** — must require action
- **Specific** — clear what's wrong and where
- **Relevant** — only alert on important issues
- **Non-noisy** — avoid alert fatigue

### Alert Tiers

| Tier | When | Examples |
|---|---|---|
| **Critical** | Immediate action | Service down, error rate > 5%, DB connection failures, payment failures |
| **Warning**  | Investigate soon | High latency (P95 > threshold), increased errors, high resource usage, slow query |
| **Info**     | Monitor          | Deployment completed, config change, scheduled maintenance |

### Prometheus Alert Rules

```yaml
groups:
  - name: application
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} requests/second"

      - alert: HighLatency
        expr: histogram_quantile(0.95, http_request_duration_seconds) > 2
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "High latency detected"
          description: "P95 latency is {{ $value }} seconds"
```

### Best Practices

- Set appropriate thresholds
- Use alert grouping to reduce noise
- Include context in messages
- Set up escalation policies
- Test alerts regularly
- Document runbooks for each alert

## Observability Stack — Recommended Tools

| Concern | Options |
|---|---|
| Logging | ELK (Elasticsearch + Logstash + Kibana), Loki + Grafana, CloudWatch, Datadog |
| Metrics | Prometheus + Grafana, CloudWatch Metrics, Datadog, New Relic |
| Tracing | Jaeger, Zipkin, OpenTelemetry, Datadog APM, New Relic |
| APM     | New Relic, Datadog APM, Elastic APM, AppDynamics |
