# Structured Logging + Metrics

## Structured Logging

### Principles

- JSON format for machine parsing
- Consistent fields (timestamp, level, message, context)
- Correlation IDs for request tracking
- Never log sensitive information
- Appropriate log levels
- Structured context

### Log Structure

```typescript
// Good: Structured logging
logger.info("User created", {
  userId: user.id,
  email: user.email,
  correlationId: request.id,
  timestamp: new Date().toISOString(),
  service: "user-service",
  action: "create",
  duration: 150,
});

// Bad: Unstructured logging
logger.info(`User ${user.id} created with email ${user.email}`);
```

### Log Levels

| Level | Purpose |
|---|---|
| ERROR | System errors, exceptions, failures |
| WARN  | Warning conditions, recoverable issues |
| INFO  | General informational messages, business events |
| DEBUG | Detailed diagnostic information |
| TRACE | Very detailed diagnostic information |

### NestJS Example with Correlation IDs

```typescript
import { Logger } from "@nestjs/common";

export class UserService {
  private readonly logger = new Logger(UserService.name);

  async createUser(data: CreateUserDto, correlationId: string) {
    const startTime = Date.now();
    this.logger.log({ message: "Creating user", correlationId, data: { email: data.email } });

    try {
      const user = await this.repository.save(data);
      this.logger.log({
        message: "User created successfully",
        correlationId,
        userId: user.id,
        duration: Date.now() - startTime,
      });
      return user;
    } catch (error) {
      this.logger.error({
        message: "Failed to create user",
        correlationId,
        error: error.message,
        stack: error.stack,
      });
      throw error;
    }
  }
}
```

### Correlation ID Middleware

```typescript
@Injectable()
export class CorrelationIdMiddleware implements NestMiddleware {
  use(req: Request, res: Response, next: NextFunction) {
    const correlationId = req.headers["x-correlation-id"] || uuidv4();
    req["correlationId"] = correlationId;
    res.setHeader("x-correlation-id", correlationId);
    next();
  }
}
```

## Metrics

### Types

| Type      | Use case                                     | Example                                                         |
|-----------|----------------------------------------------|-----------------------------------------------------------------|
| Counter   | Incrementing value (requests, errors)        | `metrics.increment("http.requests.total", { method: "GET" })`   |
| Gauge     | Current value (active connections, queue)    | `metrics.gauge("db.connections.active", connectionCount)`        |
| Histogram | Distribution (response times, sizes)         | `metrics.histogram("http.request.duration", duration)`           |
| Summary   | Histogram with quantiles                     | `metrics.summary("db.query.duration", queryTime)`                |

### Key Metrics to Track

**Application**: request rate, error rate, response time (P50/P95/P99), active sessions, business events.

**System**: CPU, memory, disk I/O, network I/O, DB connections.

**Business**: registrations, transactions, revenue, feature usage, conversion.

### Prometheus Implementation

```typescript
import { Counter, Histogram } from "prom-client";

const httpRequestsTotal = new Counter({
  name: "http_requests_total",
  help: "Total number of HTTP requests",
  labelNames: ["method", "status", "route"],
});

const httpRequestDuration = new Histogram({
  name: "http_request_duration_seconds",
  help: "Duration of HTTP requests in seconds",
  labelNames: ["method", "route"],
  buckets: [0.1, 0.5, 1, 2, 5],
});

@Injectable()
export class MetricsInterceptor implements NestInterceptor {
  intercept(context: ExecutionContext, next: CallHandler) {
    const request = context.switchToHttp().getRequest();
    const startTime = Date.now();

    return next.handle().pipe(
      tap(() => {
        const duration = (Date.now() - startTime) / 1000;
        httpRequestDuration.observe(
          { method: request.method, route: request.route?.path },
          duration,
        );
        httpRequestsTotal.inc({
          method: request.method,
          status: "200",
          route: request.route?.path,
        });
      }),
    );
  }
}
```

### Naming Conventions

- Lowercase with underscores
- Include unit when applicable
- Consistent prefixes: `http_`, `db_`, `cache_`
- Descriptive but concise

Examples: `http_requests_total`, `http_request_duration_seconds`, `database_query_duration_seconds`, `cache_hits_total`, `cache_misses_total`.
