# CODER.md

Persistent project memory for agents and developers.
Read this file at the start of every session.

Keep this file compact, durable, and project-specific. Do not use it for task logs, active plans, or one-off notes.

---

## Project Overview

**Project name:** streamXie-ui  
**Type:** Frontend streaming UI starter/template  
**Primary language(s):** TypeScript, TSX, CSS  
**Primary framework(s):** React 18, Vite, Tailwind CSS  
**Database:** none  
**Auth system:** mock/client-side UI only; no real auth provider connected  
**Deployment target:** Vercel production at `https://streamxie-ui.vercel.app`; static hosting can also serve `dist/`  
**License:** MIT

---

## Essential Commands

```bash
# Install dependencies
npm install

# Start development
npm run dev

# Build static production output
npm run build

# Preview production build locally
npm run preview

# Lint
not configured

# Typecheck
not configured as an npm script

# Test
not configured
```

---

## Repository Structure

```text
/
|-- index.html                 - Vite HTML entry point
|-- src/
|   |-- App.tsx                - React Router route map and top-level UI state
|   |-- index.tsx              - React root mount
|   |-- index.css              - global CSS variables, Tailwind layers, utilities
|   |-- assets/                - brand, avatar, poster, and content imagery
|   |-- components/
|   |   |-- common/            - app-wide reusable presentation components
|   |   |-- content/           - streaming catalog cards, hero, carousels
|   |   |-- details/           - detail-page sections
|   |   |-- layout/            - app shell, navbar, page container
|   |   |-- ui/                - Radix/Tailwind UI primitives
|   |   `-- watch/             - custom video player surface
|   |-- data/mockContent.ts    - demo catalog and filter options
|   |-- hooks/                 - document meta, auth mock, mobile, toast hooks
|   |-- lib/                   - brand constants, localStorage helpers, utilities
|   `-- pages/                 - route-level pages
|-- tailwind.config.js         - Tailwind theme extensions and token mapping
|-- vite.config.ts             - Vite config, React plugin, Tailwind PostCSS, alias
|-- FRONTEND-DNA.md            - visual and interaction rules
|-- PLAN.md                    - current/archived execution plans
|-- TODO.md                    - strategic backlog
`-- CHANGELOG.md               - completed meaningful changes
```

---

## Architecture Notes

- This is currently a frontend-only React app. Do not imply production auth, media streaming, payments, or persistence until those systems are implemented.
- Catalog content is centralized in `src/data/mockContent.ts`. Existing pages and components expect the `ContentItem`, `Season`, `Episode`, and `CastMember` shapes.
- App routing lives in `src/App.tsx` using React Router. Shared app layout wraps route pages through `AppLayout`.
- The `@` import alias maps to `src` in `vite.config.ts`.
- Demo persistence uses `localStorage` through `src/lib/storage.ts`, `src/lib/avatarStore.ts`, and `src/lib/storageKeys.ts`.
- Design tokens are defined as CSS variables in `src/index.css` and surfaced through Tailwind names in `tailwind.config.js`.
- The app uses Radix UI primitives for several base components and custom streaming-specific components for product surfaces.
- `vite.config.ts` sets `base: "./"` for static deployment compatibility.
- Repository note: `/home/fadz/projects/github/streamora` is initialized on `main` and tracks `origin` at `https://github.com/Matsumiko/streamXie-ui.git`.
- Vercel CLI project is linked locally as `novamaryat-9209s-projects/streamxie-ui`; production alias is `https://streamxie-ui.vercel.app`.
- Vercel GitHub auto-deploy integration is not connected yet because the Vercel account needs a GitHub Login Connection. CLI production deploy works.

---

## Code Style & Conventions

- Use TypeScript types for component props and data contracts.
- Keep page-level screens in `src/pages`; keep shared UI in `src/components`.
- Preserve current Tailwind-heavy styling approach and token names instead of adding a second styling system.
- Keep streaming catalog data transformations close to route pages until a real API/data layer is introduced.
- Use semantic route names and React Router `Link`/`NavLink` for internal navigation.
- Prefer existing `PageContainer`, `SectionHeader`, card, modal, toast, and layout patterns.
- Keep comments sparse; add them only when they clarify non-obvious state or browser behavior.

---

## Environment Variables

No environment variables are required for the current frontend-only demo.

When backend/API integration is added, create `.env.example` with safe placeholder names and document each variable here. Do not store real secret values in this file or in repository docs.

---

## Known Gotchas

### Frontend-only auth

**Problem:** Login, registration, reset password, and profile screens can look production-ready.  
**Why it happens:** They are UI flows only and are not connected to a backend session system.  
**How to avoid:** Document them as mock flows until a real auth provider, session handling, and security review exist.

### Mock catalog source

**Problem:** Pages import directly from `src/data/mockContent.ts`.  
**Why it happens:** The project is currently a starter/demo UI.  
**How to avoid:** Add a dedicated data adapter before replacing mock data with API calls so page components do not become tightly coupled to fetch logic.

### Local storage state

**Problem:** My List, watch progress, and avatar preferences reset per browser/profile and are not account-based.  
**Why it happens:** State is stored in browser `localStorage`.  
**How to avoid:** Replace storage helpers with backend-backed services when adding real users.

### Package scripts

**Problem:** There are no lint, test, or typecheck scripts yet.  
**Why it happens:** The project currently ships as a UI starter.  
**How to avoid:** Add scripts and CI before accepting external pull requests.
