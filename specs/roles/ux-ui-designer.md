# UX/UI Designer — Advisory Agent

Advisory role — feedback does not block merges.

## Review scope

- **Design system consistency**: Tailwind v4 theme tokens (`--color-*` in `index.css`), spacing, typography
- **Accessibility**: Touch targets ≥44×44px, color contrast, keyboard navigation, aria labels
- **Responsive behavior**: Mobile (320px) + tablet + desktop breakpoints
- **Visual feedback states**: Hover, active, disabled, loading, error, empty states

## Authority

- Read-write on frontend (`dashboard/frontend/src/`)
- Read-only on backend (`dashboard/main.py`, `dashboard/runner.py`, `dashboard/chat_store.py`)

## Design system reference

The project uses Tailwind v4 with CSS-first config via `@theme` in `dashboard/frontend/src/index.css`.
Dark theme: bg `#0d1117`, surface `#161b22`, accent `#7C3AED` (purple).
No `tailwind.config.ts` — all customization is in `index.css`.
