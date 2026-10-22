# Testing

Reference loaded on demand. Vitest + React Testing Library + MSW + Playwright.

## Test pyramid

| Layer | Tool | What | When to write |
|---|---|---|---|
| Unit | Vitest | Pure functions, hooks, utilities, schema validation | Always |
| Component | Vitest + RTL | Single component behavior with mocked APIs | Interactive UI |
| Integration | Vitest + RTL + MSW | Multi-component flows with realistic API mocking | Critical user flows |
| E2E | Playwright | Real browser, real or staged backend | Smoke + critical journeys only |

Coverage target: 80% statements, 75% branches, 100% on critical paths (auth, money, data mutations).

## Vitest config

```ts
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react-swc';
import tsconfigPaths from 'vite-tsconfig-paths';

export default defineConfig({
  plugins: [react(), tsconfigPaths()],
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    globals: false,
    coverage: {
      provider: 'v8',
      reporter: ['text', 'lcov'],
      thresholds: { statements: 80, branches: 75, functions: 80, lines: 80 },
    },
  },
});
```

## Component test - example

```tsx
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { UserForm } from './UserForm';

describe('UserForm', () => {
  it('submits valid values', async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();

    render(<UserForm onSubmit={onSubmit} />);

    await user.type(screen.getByLabelText(/name/i), 'Ada Lovelace');
    await user.type(screen.getByLabelText(/email/i), 'ada@example.com');
    await user.click(screen.getByRole('button', { name: /save/i }));

    expect(onSubmit).toHaveBeenCalledWith({
      name: 'Ada Lovelace',
      email: 'ada@example.com',
    });
  });

  it('shows validation errors for invalid email', async () => {
    const user = userEvent.setup();
    render(<UserForm onSubmit={vi.fn()} />);

    await user.type(screen.getByLabelText(/email/i), 'not-an-email');
    await user.click(screen.getByRole('button', { name: /save/i }));

    expect(await screen.findByText(/invalid email/i)).toBeInTheDocument();
  });
});
```

## Query semantics - the order

1. `getByRole` (most accessible).
2. `getByLabelText` (for form fields).
3. `getByPlaceholderText` (last resort for inputs).
4. `getByText` (for non-interactive content).
5. `getByTestId` (only as last resort - escape hatch).

Never query by class name or DOM structure.

## MSW for API mocking

```ts
import { setupServer } from 'msw/node';
import { http, HttpResponse } from 'msw';

export const handlers = [
  http.get('/api/users', () =>
    HttpResponse.json([{ id: '1', name: 'Ada' }]),
  ),
  http.post('/api/users', async ({ request }) => {
    const body = await request.json();
    return HttpResponse.json({ id: '2', ...body }, { status: 201 });
  }),
];

export const server = setupServer(...handlers);
```

Setup in `src/test/setup.ts`:

```ts
import { afterAll, afterEach, beforeAll } from 'vitest';
import { server } from './msw-server';

beforeAll(() => server.listen({ onUnhandledRequest: 'error' }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
```

Per-test override:

```ts
server.use(
  http.get('/api/users', () => HttpResponse.json([], { status: 500 })),
);
```

## Custom render with providers

```tsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, type RenderOptions } from '@testing-library/react';
import { ReactElement, ReactNode } from 'react';

function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
}

function AllProviders({ children }: Readonly<{ children: ReactNode }>) {
  const queryClient = createTestQueryClient();
  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
}

export function renderWithProviders(ui: ReactElement, options?: Omit<RenderOptions, 'wrapper'>) {
  return render(ui, { wrapper: AllProviders, ...options });
}
```

## Hook tests

```ts
import { renderHook, act, waitFor } from '@testing-library/react';
import { useDebouncedValue } from './useDebouncedValue';

it('debounces value changes', async () => {
  const { result, rerender } = renderHook(
    ({ value }) => useDebouncedValue(value, 100),
    { initialProps: { value: 'a' } },
  );

  expect(result.current).toBe('a');
  rerender({ value: 'b' });
  expect(result.current).toBe('a');
  await waitFor(() => expect(result.current).toBe('b'));
});
```

## Playwright - E2E

```ts
import { test, expect } from '@playwright/test';

test('user can create a new lawyer', async ({ page }) => {
  await page.goto('/login');
  await page.getByLabel('Email').fill('admin@oabprev.org');
  await page.getByLabel('Password').fill(process.env.TEST_PASSWORD!);
  await page.getByRole('button', { name: /sign in/i }).click();

  await expect(page).toHaveURL('/dashboard');
  await page.getByRole('link', { name: /lawyers/i }).click();
  await page.getByRole('button', { name: /add lawyer/i }).click();
  await page.getByLabel('Name').fill('Ada Lovelace');
  await page.getByRole('button', { name: /save/i }).click();

  await expect(page.getByRole('row', { name: /ada lovelace/i })).toBeVisible();
});
```

Run E2E only on critical paths - they are slow and flaky compared to unit/component tests. Use `playwright.config.ts` `projects` for cross-browser.

## What NOT to test

- Implementation details (private methods, internal state shape).
- Third-party libs (assume RHF, TanStack Query, shadcn work).
- Trivial getters/setters.
- Snapshot tests for everything (use sparingly - they rot).

## Test naming

`should <expected behavior> when <condition>`. Always present tense. English (per project rule).

```ts
it('should disable submit when form is invalid', () => { /* ... */ });
```

## Flaky test policy

A flaky test is a broken test. Quarantine immediately, fix or delete within 48h. Never `retry()` to mask flakiness.
