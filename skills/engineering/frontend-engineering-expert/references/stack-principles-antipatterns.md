## Default stack (use unless project says otherwise)

- **Build**: Vite 5+ (React plugin + SWC)
- **Framework**: React 19 with hooks
- **Language**: TypeScript strict
- **Styling**: Tailwind CSS v3+ with shadcn/ui primitives (Radix under the hood)
- **State (server)**: TanStack Query v5
- **State (UI)**: Zustand for cross-tree, `useState`/`useReducer` for local
- **Routing**: TanStack Router (type-safe) or React Router v6
- **Forms**: React Hook Form + Zod (single schema for validation + types)
- **HTTP**: Axios or native `fetch` wrapped in a typed client
- **Testing**: Vitest + React Testing Library + MSW + Playwright (E2E)
- **Icons**: lucide-react
- **Motion**: framer-motion (only when it improves UX, not for show)

## Non-negotiable principles

1. **Mobile-first ALWAYS**: design and code for the smallest viewport first, scale up with `sm:` `md:` `lg:` breakpoints. Test at 375px width before anything else.
2. **Component props are `Readonly`**: every prop interface uses `Readonly<>` (sonarqube `typescript:S6759`). Apply at the type level.
3. **No `any`**: never. Use `unknown` and narrow, or define proper types.
4. **`??` not `||`** for default values (so `0`, `''`, `false` are preserved).
5. **`Promise.all` for independent async**: never sequential `await` when calls do not depend on each other. Use `Promise.allSettled` to keep going on failures.
6. **No code comments**: code must be self-documenting via naming. Only document non-obvious intent (the why, never the what).
7. **Strict TypeScript**: no implicit any, no unchecked indexed access slip-throughs, exhaustive switches via `never` checks.
8. **Server state vs UI state**: server state lives in TanStack Query (cached, revalidated). UI state (modal open, form draft) lives in component or Zustand. Never mix.
9. **Accessibility is a feature, not a checkbox**: WCAG 2.2 AA minimum. Keyboard, screen reader, focus management, contrast.
10. **Bundle size matters**: every dependency is a budget cost. Prefer native APIs and tree-shakable imports.

## Anti-patterns - reject these on sight

- `useEffect` for derived state (use `useMemo` or compute inline).
- `useEffect` to fetch data on mount (use TanStack Query).
- `React.FC` (use plain function with typed props).
- Inline arrow functions as JSX props in lists (causes re-renders; memoize).
- `index` as `key` in lists when items can reorder.
- Mixing `dangerouslySetInnerHTML` with user input.
- Custom CSS files when Tailwind utility composition would do.
- Importing entire libraries (`import _ from 'lodash'`) instead of named/per-function imports.
- Sequential `await` in unrelated calls (use `Promise.all`).
- Missing loading/error/empty states. Every async UI MUST handle all four states (idle/loading/error/success-empty/success-data).

## Output style

- Concise PR-ready code. No prose explanations inside files.
- When proposing changes, lead with the diff, not the discussion.
- When creating new components, suggest a path consistent with the project layout discovered in Phase 0.
- After implementation, update relevant `docs/` files if architecture changed (per `AGENTS.md` rule).

