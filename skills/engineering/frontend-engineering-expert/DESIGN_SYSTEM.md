# Design System

Reference loaded on demand. Tailwind + shadcn/ui composition for production UIs.

## Tailwind tokens (extend in `tailwind.config.ts`)

Use semantic tokens, not hex codes scattered across components:

```ts
extend: {
  colors: {
    background: 'hsl(var(--background))',
    foreground: 'hsl(var(--foreground))',
    primary: { DEFAULT: 'hsl(var(--primary))', foreground: 'hsl(var(--primary-foreground))' },
    muted: { DEFAULT: 'hsl(var(--muted))', foreground: 'hsl(var(--muted-foreground))' },
    destructive: { DEFAULT: 'hsl(var(--destructive))', foreground: 'hsl(var(--destructive-foreground))' },
    border: 'hsl(var(--border))',
    ring: 'hsl(var(--ring))',
  },
  borderRadius: { lg: 'var(--radius)', md: 'calc(var(--radius) - 2px)', sm: 'calc(var(--radius) - 4px)' },
}
```

CSS variables in `app/globals.css` define light + dark themes. Never hardcode `bg-blue-500` in business components - always use semantic tokens.

## shadcn/ui composition

Install components into your repo (they are NOT a npm dep):

```bash
pnpm dlx shadcn@latest add button input form dialog dropdown-menu toast
```

Customize in your codebase. Compose, do not subclass:

```tsx
<Button variant="destructive" size="sm" className="gap-2">
  <Trash className="h-4 w-4" /> Delete
</Button>
```

Use `cn()` (clsx + tailwind-merge) for conditional classes:

```tsx
import { cn } from '@/lib/utils';

<div className={cn('rounded-lg border p-4', isActive && 'border-primary bg-primary/5')} />
```

## Mobile-first responsive

Default styles target mobile. Use breakpoints to scale up:

```tsx
<div className="flex flex-col gap-4 md:flex-row md:gap-6 lg:gap-8">
  <aside className="w-full md:w-64" />
  <main className="flex-1" />
</div>
```

Test at: 375px (mobile), 768px (tablet), 1024px (desktop), 1440px (wide).

## Dark mode

Use `next-themes` (works with Vite via context provider). Toggle via `class="dark"` on `<html>`. Tailwind respects via `darkMode: 'class'`.

```tsx
const { theme, setTheme } = useTheme();
```

Test EVERY screen in both themes. No exceptions.

## Accessibility - WCAG 2.2 AA

- Semantic HTML first: `<button>` not `<div onClick>`. `<nav>` for navigation. `<main>` once per page.
- Labels: every input has a `<Label>` linked via `htmlFor` (or wrapped). shadcn `<FormLabel>` does this.
- Focus management: trap focus in modals (Radix does this), restore focus on close, visible focus ring (`ring-2 ring-ring`).
- Color contrast: minimum 4.5:1 for body text, 3:1 for large text. Verify with browser DevTools.
- Alt text: every `<img>` has `alt`. Decorative images use `alt=""`.
- ARIA: only when semantic HTML cannot express it. Wrong ARIA is worse than none.
- Keyboard navigation: every interactive element reachable via Tab; activated via Enter/Space.
- Skip links: provide "Skip to main content" at top of every page.
- Reduced motion: respect `prefers-reduced-motion` in animations.

```tsx
const reducedMotion = useReducedMotion();
<motion.div animate={reducedMotion ? {} : { opacity: 1 }} />
```

## Spacing scale

Use Tailwind's 4px scale exclusively: `gap-2` (8px), `gap-4` (16px), `gap-6` (24px), `gap-8` (32px). Never `mt-[13px]`.

## Typography

Define sizes in `tailwind.config.ts`. Use `text-sm`, `text-base`, `text-lg`, `text-xl`, etc. Pair with `leading-*` for line height. Body text: `text-sm md:text-base`. Headings: `text-2xl font-semibold tracking-tight`.

## Motion - sparingly

Use `framer-motion` for state transitions that improve UX comprehension (modal enter/exit, toast slide-in, layout shifts). Never decorative. Always respect `prefers-reduced-motion`.

```tsx
<motion.div
  initial={{ opacity: 0, y: 8 }}
  animate={{ opacity: 1, y: 0 }}
  transition={{ duration: 0.18, ease: 'easeOut' }}
/>
```

Default duration: 150-200ms for UI; 300ms max for hero motion.

## States to design (every component)

For any interactive surface, design ALL of:
- default
- hover
- focus-visible
- active
- disabled
- loading
- error
- empty (when applicable to data display)

Use `aria-busy="true"` and disable interaction during loading.

## Empty states

Never show a blank page. Provide:
- Illustration or icon (`lucide-react`).
- Headline + 1-line explanation.
- Primary action ("Create your first X") when applicable.

## Forms layout

- One column on mobile, multi-column only on `md:` and above.
- Labels above inputs (better mobile UX than left-aligned).
- Errors inline, below input, in `text-destructive`.
- Submit button right-aligned in modal/dialog footer; full-width on mobile.

## Color usage

- `primary`: brand action color (1 per page maximum for primary CTA).
- `secondary`: less prominent actions.
- `destructive`: delete/dangerous actions (NEVER for cancel buttons).
- `muted`: backgrounds for non-interactive surfaces, hint text via `muted-foreground`.

## Density modes

Provide compact/comfortable toggles only when the user has long sessions with dense data (admin tables, dashboards). Default to comfortable.
