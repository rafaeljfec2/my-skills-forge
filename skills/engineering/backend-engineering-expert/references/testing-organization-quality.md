## Testing

### Unit Tests

- Test business logic in isolation
- Mock external dependencies
- Aim for high coverage of critical paths
- Test edge cases and error scenarios
- Keep tests fast and independent

### Integration Tests

- Test API endpoints end-to-end
- Test database interactions
- Test service integrations
- Use test databases
- Clean up test data

### Test Structure

- Arrange-Act-Assert pattern
- Descriptive test names
- Test one thing per test
- Use factories/fixtures for test data
- Keep tests maintainable

## Code Organization

### Project Structure

```
src/
├── modules/           # Feature modules
│   ├── users/
│   │   ├── dto/
│   │   ├── entities/
│   │   ├── users.controller.ts
│   │   ├── users.service.ts
│   │   └── users.module.ts
├── common/            # Shared utilities
├── config/            # Configuration
└── main.ts
```

### Best Practices

- Group by feature, not by type
- Keep modules focused and cohesive
- Extract shared logic to common modules
- Use barrel exports carefully
- Maintain clear dependency direction
- Keep files focused (single responsibility)

## Error Handling

### Strategy

- Use custom exception classes
- Implement global exception filters
- Return appropriate HTTP status codes
- Provide meaningful error messages
- Log errors with context
- Don't expose internal errors to clients
- Handle async errors properly

### Patterns

```typescript
// Custom exceptions
class NotFoundException extends HttpException {
  constructor(resource: string) {
    super(`${resource} not found`, HttpStatus.NOT_FOUND);
  }
}

// Global exception filter
@Catch()
export class AllExceptionsFilter implements ExceptionFilter {
  catch(exception: unknown, host: ArgumentsHost) {
    // Handle and format errors
  }
}
```

## Code Quality Checklist

When reviewing or writing backend code, ensure:

- [ ] Code follows clean code principles
- [ ] Functions are small and focused
- [ ] Naming is clear and descriptive
- [ ] Error handling is comprehensive
- [ ] Security best practices are followed
- [ ] Performance considerations are addressed
- [ ] Tests are present and meaningful
- [ ] Documentation is clear
- [ ] Dependencies are minimized
- [ ] Code is maintainable and extensible
