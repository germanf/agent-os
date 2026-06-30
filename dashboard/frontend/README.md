# Twitter Exporter Dashboard — Frontend

React 19 SPA, TypeScript, Tailwind v4, Vite 8.

## Quick start

```bash
pnpm install        # install dependencies
pnpm run dev        # Vite dev server (proxies /api and /auth to :8765)
pnpm run build      # tsc -b && vite build → dist/
pnpm run test       # vitest
pnpm run test:coverage  # vitest --coverage
pnpm run lint       # eslint
```

## Dev proxy

`vite.config.ts` proxies `/api/*` and `/auth/*` to `http://127.0.0.1:8765` (uvicorn dev server).

## Routes (React Router)

| Path | Component | Description |
|------|-----------|-------------|
| `/` | Landing | Navigation hub |
| `/scrapers` | Scrapers | Twitter API v2 + Playwright scraper |
| `/resumen` | Resumen | Condensed stats from analyzed Twitter data |
| `/notes` | Notes | Obsidian vault browser |
| `/chat` | Chat | Chat list (no active chat) |
| `/chat/:chatId` | Chat | Active chat with Claude |

## Project structure

```
src/
├── main.tsx             Entrypoint
├── App.tsx              Routes
├── index.css            Tailwind + theme vars
├── components/          Shared components (Layout, ChatSidebar, etc.)
├── pages/               Page components (Landing, Scrapers, Resumen, Notes, Chat)
├── lib/                 Helpers (api, sanitize, speech, clipboard, uuid, useToolJob)
└── test/                Test setup (vitest + jsdom)
```

## Tech

- React 19, react-router-dom 7
- Tailwind v4 (CSS-first config via `@theme` in `index.css`, no `tailwind.config.ts`)
- marked + DOMPurify for Markdown rendering (XSS-safe)
- vitest + @testing-library/react + jsdom for tests
