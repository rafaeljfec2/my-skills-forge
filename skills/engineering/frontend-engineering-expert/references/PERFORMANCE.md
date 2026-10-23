# Performance

Reference loaded on demand. Web Vitals targets and how to hit them.

## Web Vitals - production targets

| Metric | Target | What it measures |
|---|---|---|
| LCP (Largest Contentful Paint) | < 2.5s | Time to render the largest visible element |
| INP (Interaction to Next Paint) | < 200ms | Responsiveness to user input |
| CLS (Cumulative Layout Shift) | < 0.1 | Visual stability |
| FCP (First Contentful Paint) | < 1.8s | First paint of any content |
| TTFB (Time To First Byte) | < 0.8s | Server responsiveness |

Measure with Lighthouse CI in PRs and `web-vitals` lib in production.

## Bundle size budget

| Asset | Budget |
|---|---|
| Initial JS (gzipped) | < 150 KB |
| Initial CSS (gzipped) | < 30 KB |
| Per-route JS chunk | < 50 KB |
| Largest image | < 200 KB (use WebP/AVIF) |

Enforce via `vite-bundle-visualizer` or `rollup-plugin-visualizer`. Add CI check.

## Code splitting

- Route-level: lazy import every route component.
- Component-level: lazy import heavy non-critical widgets (charts, rich editors, maps).
- Vendor splitting: Vite does this automatically; verify with bundle visualizer.

```tsx
const Chart = lazy(() => import('@/components/Chart'));

<Suspense fallback={<ChartSkeleton />}>
  <Chart data={data} />
</Suspense>
```

## Tree shaking - import surgically

```tsx
// BAD
import _ from 'lodash';
import * as icons from 'lucide-react';

// GOOD
import debounce from 'lodash/debounce';
import { ChevronRight, User } from 'lucide-react';
```

For shadcn/Radix: already tree-shaken by default. For date libs prefer `date-fns` (per-function imports) over `moment`.

## Image optimization

- Format: AVIF first, WebP fallback, original last.
- Responsive: use `srcset` + `sizes`. For React, consider `vite-imagetools`.
- Lazy load below the fold: `loading="lazy"` + `decoding="async"`.
- Hero image: preload via `<link rel="preload" as="image">`.
- Always set `width` and `height` to prevent CLS.

```tsx
<img
  src={hero}
  width={1200}
  height={600}
  loading="eager"
  fetchPriority="high"
  alt="Dashboard overview"
/>
```

## Virtualization

Lists with >100 visible-eligible items: use `@tanstack/react-virtual`.

```tsx
const rowVirtualizer = useVirtualizer({
  count: items.length,
  getScrollElement: () => parentRef.current,
  estimateSize: () => 48,
  overscan: 5,
});
```

## React render perf

- Avoid creating objects/arrays in JSX props (`style={{...}}`, `data={[]}`).
- `key` is unique and stable (not array index for reorderable lists).
- Heavy children: extract and `memo`.
- Context providers: split state and dispatch contexts to avoid all-children re-renders on state change.
- React 19's compiler memoizes most cases; profile before adding `useMemo`/`useCallback` manually.

## Network

- TanStack Query `staleTime` non-zero for queries that do not need real-time freshness (default `staleTime: 30_000`).
- HTTP/2 multiplexing - many small requests are fine.
- Avoid waterfalls: prefetch on hover (`onMouseEnter` -> `queryClient.prefetchQuery`).
- Use TanStack Router loaders to parallel-fetch route data with code download.

## Avoid blocking the main thread

- Heavy computation: web worker (`comlink` makes it ergonomic).
- JSON.parse of >100KB payloads: stream or web worker.
- Long lists: virtualize.
- Animations: prefer CSS transforms (GPU-accelerated) over JS-driven `top`/`left`.

## Measuring in dev

- Chrome DevTools Performance panel: record interactions, look for long tasks (>50ms).
- React DevTools Profiler: identify expensive renders.
- Lighthouse: run in incognito with throttling to simulate real users.
- `web-vitals` lib in production: report to your analytics.

```ts
import { onCLS, onINP, onLCP } from 'web-vitals';

onCLS(console.log);
onINP(console.log);
onLCP(console.log);
```

## CI gates

- Lighthouse CI with budget JSON enforcing the targets above.
- Bundle size diff comment on PRs (e.g., `size-limit` action).
- Block merge if budget exceeded by >10% without justification.
