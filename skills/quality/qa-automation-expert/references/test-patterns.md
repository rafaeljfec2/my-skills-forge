# Test Patterns — Determinism, Isolation, Mocking

## Determinism

- Same input → same output
- No external state, time, or random
- No real network/file I/O (unless mocked)

### Anti-pattern: time-dependent

```typescript
// Bad
test("should expire token", () => {
  const token = createToken();
  setTimeout(() => {
    expect(token.isExpired()).toBe(true);
  }, 1000);
});

// Good
test("should expire token", () => {
  const expiredDate = new Date("2020-01-01");
  const token = createToken({ expiresAt: expiredDate });
  expect(token.isExpired()).toBe(true);
});
```

### Anti-pattern: random data

```typescript
// Bad
test("should generate user", () => {
  const user = generateUser();
  expect(user.name).toBeDefined();
});

// Good
test("should generate user", () => {
  const user = generateUser({ name: "John Doe" });
  expect(user.name).toBe("John Doe");
});
```

## Isolation

- Each test independent of execution order
- No shared mutable state
- Clean up after each test
- Use setup/teardown hooks

```typescript
describe("UserService", () => {
  let service: UserService;
  let repository: UserRepository;

  beforeEach(() => {
    repository = new MockUserRepository();
    service = new UserService(repository);
  });

  afterEach(() => {
    repository.clear();
  });

  test("should create user", async () => {
    const user = await service.create({ name: "John" });
    expect(user.id).toBeDefined();
  });
});
```

Techniques: mocks/stubs for external deps; test DBs (in-memory or isolated); reset state between tests; factories/fixtures for data; avoid global state.

## AAA Pattern (Arrange-Act-Assert)

```typescript
test("should calculate total price", () => {
  // Arrange
  const items = [
    { price: 10, quantity: 2 },
    { price: 5, quantity: 3 },
  ];

  // Act
  const total = calculateTotal(items);

  // Assert
  expect(total).toBe(35);
});
```

## Mocking and Stubbing

### When to mock

External APIs · DB ops in unit tests · file system · time-dependent functions · RNG · network requests.

### Examples

```typescript
// Mock external service
jest.mock("../services/paymentService", () => ({
  processPayment: jest.fn().mockResolvedValue({ success: true }),
}));

// Mock repository
const mockRepository = {
  findOne: jest.fn(),
  save: jest.fn(),
  delete: jest.fn(),
};

test("should process order", async () => {
  mockRepository.findOne.mockResolvedValue({ id: "1", status: "pending" });
  mockRepository.save.mockResolvedValue({ id: "1", status: "completed" });

  const result = await orderService.completeOrder("1");
  expect(result.status).toBe("completed");
  expect(mockRepository.save).toHaveBeenCalled();
});
```

## Factories / Fixtures

```typescript
export const createUser = (overrides = {}) => ({
  id: "1",
  name: "John Doe",
  email: "john@example.com",
  ...overrides,
});

test("should update user", async () => {
  const user = createUser({ name: "Jane Doe" });
  const updated = await service.update(user.id, { name: "Jane Smith" });
  expect(updated.name).toBe("Jane Smith");
});
```
