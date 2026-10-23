# React Patterns

Reference loaded on demand. Production patterns for React 19 + TypeScript.

## Component file template

```tsx
import { z } from 'zod';

const userFormSchema = z.object({
  name: z.string().min(1, 'Name required'),
  email: z.string().email('Invalid email'),
});

type UserFormValues = z.infer<typeof userFormSchema>;

type UserFormProps = Readonly<{
  defaultValues?: UserFormValues;
  onSubmit: (values: UserFormValues) => void | Promise<void>;
}>;

export function UserForm({ defaultValues, onSubmit }: UserFormProps) {
  // Implementation
}
```

Order inside the file: imports -> schemas -> types -> helper functions -> hooks -> component -> default export (only if router demands).

## Hooks rules

- Names start with `use`.
- Return tuples for state-pair returns: `[value, setValue]`.
- Return objects for >2 values: `{ data, isLoading, error }`.
- Custom hooks own their cleanup (return `useEffect` cleanup).
- Never put hooks inside conditionals or loops.

## Server state - TanStack Query v5

```tsx
const usersQuery = useQuery({
  queryKey: ['users', { search, page }] as const,
  queryFn: () => api.users.list({ search, page }),
  staleTime: 30_000,
});
```

Conventions:
- Query keys are arrays starting with the resource name. Use `as const` for inference.
- Centralize `queryKeys` in `src/lib/queryKeys.ts` to avoid drift.
- Mutations use `onMutate` for optimistic updates, `onError` for rollback, `onSettled` for invalidation.
- Use `useSuspenseQuery` when the route guarantees data via loaders.

## UI state - Zustand only when shared across tree

```tsx
type UiStore = {
  sidebarOpen: boolean;
  toggleSidebar: () => void;
};

export const useUiStore = create<UiStore>((set) => ({
  sidebarOpen: false,
  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
}));
```

Local state stays in `useState`/`useReducer`. Lift to context only when needed by a subtree (theme, locale). Lift to Zustand only when needed across unrelated trees.

## Forms - React Hook Form + Zod

Single schema is the source of truth for validation AND types:

```tsx
const form = useForm<UserFormValues>({
  resolver: zodResolver(userFormSchema),
  defaultValues,
});

const handleSubmit = form.handleSubmit(async (values) => {
  await onSubmit(values);
});
```

Always use `Controller` for shadcn/Radix components that do not natively integrate with RHF refs.

## Suspense + Error Boundaries

Wrap async UI:

```tsx
<ErrorBoundary fallback={<ErrorState />}>
  <Suspense fallback={<Skeleton />}>
    <UsersList />
  </Suspense>
</ErrorBoundary>
```

Use `react-error-boundary` package. Reset boundaries on route change.

## Code splitting

Route-level by default with TanStack Router lazy routes:

```tsx
export const Route = createFileRoute('/admin/users')({
  loader: ({ context }) => context.queryClient.ensureQueryData(usersQueryOptions()),
  component: lazy(() => import('./users.page')),
});
```

Component-level only for heavy widgets (charts, editors, maps).

## Effects - the rule

If you can derive it, do not store it. If you can compute it, do not effect it.

```tsx
const fullName = `${user.firstName} ${user.lastName}`;
const filtered = useMemo(() => items.filter(byStatus(status)), [items, status]);
```

Legitimate `useEffect` use cases: subscribing to external systems (websockets, browser APIs, third-party SDKs), syncing with non-React state.

## Memoization budget

Default: do not memoize. React 19's compiler handles most cases. Add `memo`, `useMemo`, `useCallback` only when:
- Profiler shows a render is hot.
- Stable reference needed for downstream `useEffect` / context.
- List of >50 items where a child renders are expensive.

## Async handling

```tsx
const [users, posts] = await Promise.all([fetchUsers(), fetchPosts()]);
```

For partial-failure tolerance:

```tsx
const results = await Promise.allSettled([fetchA(), fetchB()]);
```

## Exhaustive switches

```tsx
function statusLabel(status: UserStatus): string {
  switch (status) {
    case 'active': return 'Active';
    case 'suspended': return 'Suspended';
    default: {
      const _exhaustive: never = status;
      throw new Error(`Unhandled status: ${String(_exhaustive)}`);
    }
  }
}
```
