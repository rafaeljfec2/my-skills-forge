# Integration Tests + Critical Flows + CI

## Integration Testing

### Principles

- Test real interactions between components
- Use isolated test databases
- Test API endpoints
- Test DB operations
- Clean up data after each test

### NestJS Example

```typescript
describe("UserController (integration)", () => {
  let app: INestApplication;
  let database: TestDatabase;

  beforeAll(async () => {
    database = await setupTestDatabase();
    const module = await Test.createTestingModule({
      imports: [AppModule],
    })
      .overrideProvider(Database)
      .useValue(database)
      .compile();
    app = module.createNestApplication();
    await app.init();
  });

  afterAll(async () => {
    await database.cleanup();
    await app.close();
  });

  test("POST /users should create user", async () => {
    const response = await request(app.getHttpServer())
      .post("/users")
      .send({ name: "John", email: "john@example.com" })
      .expect(201);

    expect(response.body).toMatchObject({
      id: expect.any(String),
      name: "John",
      email: "john@example.com",
    });
  });
});
```

## Critical Flows

### Identify

User registration & auth · payment processing · CRUD · business rule enforcement · security-sensitive operations.

### Scenarios per flow

1. **Happy path** — normal successful flow
2. **Error cases** — invalid inputs, failures
3. **Edge cases** — boundary conditions, limits
4. **Security** — authorization, validation
5. **Performance** — response times, load

### Example

```typescript
describe("User Registration Flow", () => {
  test("should register user successfully", async () => {
    const result = await registerUser({
      email: "user@example.com",
      password: "SecurePass123!",
    });
    expect(result.success).toBe(true);
    expect(result.user.email).toBe("user@example.com");
  });

  test("should reject weak password", async () => {
    await expect(
      registerUser({ email: "user@example.com", password: "123" }),
    ).rejects.toThrow("Password too weak");
  });

  test("should reject duplicate email", async () => {
    await registerUser({ email: "existing@example.com", password: "SecurePass123!" });
    await expect(
      registerUser({ email: "existing@example.com", password: "SecurePass123!" }),
    ).rejects.toThrow("Email already exists");
  });
});
```

## CI/CD Integration

### Pipeline Stages

1. **Lint** — code quality
2. **Unit Tests** — fast, isolated
3. **Integration Tests** — component interactions
4. **E2E Tests** — full flows (optional, can be scheduled)
5. **Coverage Report** — generate and publish

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: "18"

      - name: Install dependencies
        run: yarn install

      - name: Run linter
        run: yarn lint

      - name: Run unit tests
        run: yarn test:unit

      - name: Run integration tests
        run: yarn test:integration
        env:
          DATABASE_URL: ${{ secrets.TEST_DATABASE_URL }}

      - name: Generate coverage
        run: yarn test:coverage

      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

### Test Commands

```json
{
  "scripts": {
    "test": "jest",
    "test:unit": "jest --testPathPattern=unit",
    "test:integration": "jest --testPathPattern=integration",
    "test:e2e": "jest --testPathPattern=e2e",
    "test:watch": "jest --watch",
    "test:coverage": "jest --coverage",
    "test:ci": "jest --ci --coverage --maxWorkers=2"
  }
}
```

## Test Organization

```
src/
├── users/
│   ├── users.service.ts
│   ├── users.service.spec.ts      # Unit tests
│   ├── users.controller.ts
│   └── users.controller.spec.ts
├── __tests__/
│   ├── integration/
│   │   └── users.integration.spec.ts
│   └── e2e/
│       └── user-registration.e2e.spec.ts
```

### Naming

- Unit: `*.spec.ts` or `*.test.ts` alongside source
- Integration: `*.integration.spec.ts` in `__tests__/integration/`
- E2E: `*.e2e.spec.ts` in `__tests__/e2e/`
