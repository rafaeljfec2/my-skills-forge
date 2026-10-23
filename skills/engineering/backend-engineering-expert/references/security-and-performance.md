## Security

### Authentication & Authorization

- Implement JWT-based authentication
- Use refresh tokens for session management
- Enforce role-based access control (RBAC)
- Validate permissions at multiple layers
- Secure password storage (hashing, salting)
- Implement rate limiting
- Protect against brute force attacks

### Data Protection

- Validate and sanitize all inputs
- Use parameterized queries (prevent SQL injection)
- Encrypt sensitive data at rest and in transit
- Implement CORS properly
- Use HTTPS everywhere
- Protect against XSS and CSRF
- Secure API keys and secrets (use environment variables)
- Implement proper error handling (don't leak sensitive info)

## Performance Optimization

### Database

- Design efficient schemas and indexes
- Optimize queries (avoid N+1 problems)
- Use connection pooling
- Implement caching strategies (Redis, in-memory)
- Consider read replicas for scaling reads
- Use database transactions appropriately
- Batch operations when possible
- Monitor slow queries

### Application

- Use async/await properly
- Avoid blocking operations
- Implement request queuing when needed
- Use compression (gzip, brotli)
- Optimize JSON serialization
- Cache frequently accessed data
- Use CDN for static assets
- Implement lazy loading where appropriate
