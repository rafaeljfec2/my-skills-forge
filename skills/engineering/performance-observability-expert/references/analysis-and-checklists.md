## Performance Analysis

### Common Bottlenecks

- Database queries (N+1, missing indexes, full table scans)
- External API calls (slow responses, timeouts)
- CPU-intensive operations (synchronous processing)
- Memory issues (leaks, excessive allocations)
- Network latency (geographic distance, bandwidth)
- I/O operations (file system, disk access)

### Analysis Techniques

Profiling (CPU, memory) · Database query analysis · Network monitoring · APM · Load testing.

### Latency Metrics

| Metric | Meaning |
|---|---|
| Response Time | Time to process and return response |
| P50/P95/P99   | Percentiles showing latency distribution |
| Throughput    | Requests per second |
| Error Rate    | Percentage of failed requests |

Measure at: end-to-end request, database query, external API call, internal service call, processing time.

### Optimization Strategies

**Database**: appropriate indexes; optimize queries (avoid N+1, use joins); connection pooling; caching; read replicas; query analysis tools.

**Application**: async/await for I/O; caching (Redis, in-memory); algorithm complexity reduction; pagination for large datasets; request queuing; compression (gzip, brotli).

**Infrastructure**: horizontal scaling; load balancing; CDN for static assets; database optimization; network optimization.

## Detailed Implementation

For implementation patterns and code samples, follow the references:

- `references/logging-and-metrics.md` — structured logging principles, log levels, NestJS examples, correlation IDs, metric types (Counter/Gauge/Histogram/Summary), Prometheus implementation, naming conventions.
- `references/tracing-queries-alerts.md` — OpenTelemetry tracing, context propagation, query optimization (N+1, indexes, EXPLAIN), Prometheus alert rules, observability stack recommendations.

## Performance Checklist

- [ ] Database queries optimized (indexes, no N+1)
- [ ] Caching implemented where appropriate
- [ ] Async operations used for I/O
- [ ] Response times measured and tracked
- [ ] Slow queries identified and optimized
- [ ] Resource usage monitored
- [ ] Load testing performed
- [ ] Bottlenecks identified and addressed

## Observability Checklist

- [ ] Structured logging implemented
- [ ] Correlation IDs added
- [ ] Key metrics defined and tracked
- [ ] Distributed tracing configured
- [ ] Alerts configured for critical issues
- [ ] Dashboards created for monitoring
- [ ] Log aggregation set up
- [ ] Performance baselines established

## Performance Review Template

```markdown
# Performance Analysis: [Component/Feature]

## Current Performance

- Response Time (P50/P95/P99): [values]
- Throughput: [requests/second]
- Error Rate: [percentage]

## Bottlenecks Identified

- [Bottleneck 1]: [Impact, Solution]
- [Bottleneck 2]: [Impact, Solution]

## Optimizations Applied

- [Optimization 1]: [Expected improvement]
- [Optimization 2]: [Expected improvement]

## Metrics to Monitor

- [Metric 1]: [Threshold]
- [Metric 2]: [Threshold]

## Alerts Configured

- [Alert 1]: [Condition]
- [Alert 2]: [Condition]
```
