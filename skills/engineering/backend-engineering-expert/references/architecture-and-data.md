## Service Architecture

### Decoupled Services

- Define clear service boundaries
- Use interfaces/contracts between services
- Minimize direct dependencies
- Implement service discovery
- Use API gateways for routing
- Design for failure (circuit breakers, retries)
- Implement health checks

### Microservices Patterns

- Single responsibility per service
- Independent deployment
- Database per service
- Event-driven communication
- Saga pattern for distributed transactions
- API composition for aggregating data

## Data Modeling

### Database Design

- Normalize appropriately (avoid over-normalization)
- Design indexes strategically
- Consider partitioning for large tables
- Plan for data growth
- Use appropriate data types
- Design for query patterns
- Consider read vs write patterns

### Data Access

- Use repositories/data access layers
- Implement proper transaction management
- Handle migrations carefully
- Use ORMs effectively (avoid N+1, optimize queries)
- Consider caching layers
- Implement data validation at multiple levels
