<!-- GSD:project-start source:PROJECT.md -->
## Project

**Project Context**

NutriSnap is an AI-powered fitness and nutrition tracking web application. It uses artificial intelligence to identify food from photos and automatically tracks daily nutrition. Unlike traditional trackers, NutriSnap is designed to remove the hassle of diet tracking while keeping users engaged through robust gamification (streaks, badges, XP, levels). It is accessible for beginners to advanced gym-goers and offers full offline capabilities (PWA).

**Core Value:** The single most important objective is to make fitness easy without hassle — allowing users to log meals with nothing more than a photo snap.
<!-- GSD:project-end -->

<!-- GSD:stack-start source:codebase/STACK.md -->
## Technology Stack

## Languages & Runtime
| Technology | Version | Notes |
|-----------|---------|-------|
| JavaScript (JSX) | ES2020+ | ES modules (`"type": "module"`) |
| CSS | Vanilla | No preprocessors or utility frameworks |
| HTML | 5 | Standard entry points |
## Frameworks & Libraries
### Root Project (`/`)
| Dependency | Version | Purpose |
|-----------|---------|---------|
| React | ^18.2.0 | UI framework |
| React DOM | ^18.2.0 | DOM renderer |
| Vite | ^5.0.0 | Build tool / Dev server |
### `nutrisnap-new/` Sub-project
| Dependency | Version | Purpose |
|-----------|---------|---------|
| React | ^19.2.4 | UI framework (newer major version) |
| React DOM | ^19.2.4 | DOM renderer |
| Recharts | ^3.8.1 | Charting library (BarChart for nutrition data) |
| Vite | ^8.0.1 | Build tool / Dev server |
| ESLint | ^9.39.4 | Linting |
| @vitejs/plugin-react | ^6.0.1 | React support for Vite |
## Fonts
- **Fredoka** (400, 500, 600) — Headings, branding
- **Poppins** (300, 400, 500, 600) — Body text (root project)
- **Nunito** (400, 600, 700) — Body text (nutrisnap-new)
## Build & Dev
| Script | Command | Notes |
|--------|---------|-------|
| `dev` | `vite` | Local dev server with HMR |
| `build` | `vite build` | Production build |
| `preview` | `vite preview` | Preview production build |
| `lint` | `eslint .` | Only in `nutrisnap-new/` |
## Configuration
- `vite.config.js` — Minimal: only `@vitejs/plugin-react` plugin
- No TypeScript configuration
- No environment variable files (`.env`) found
- No path aliases configured
## Key Observations
- **Two separate Vite projects** exist in the workspace: root (`/`) and `nutrisnap-new/`
- Root project uses React 18, `nutrisnap-new` uses React 19 — version mismatch
- Both projects have their own `node_modules/`, `package.json`, and `vite.config.js`
- No routing library installed (everything is in a single `App.jsx`)
- No state management library (only React `useState`)
- No CSS preprocessors or utility frameworks (all vanilla CSS)
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

## Code Style
### JavaScript/JSX
- No TypeScript — pure JavaScript with JSX
- ES module imports (`import ... from ...`)
- Functional components only (no class components)
- Arrow functions for event handlers and callbacks
- Inline event handlers in JSX (`onClick={()=>setState(true)}`)
- No semicolons (inconsistent — some files use them, others don't)
- Single quotes for strings
- Minimal whitespace in JSX attributes (`className="card"`)
### CSS
- Vanilla CSS only (no Sass, Less, CSS Modules, or Tailwind)
- Class-based selectors (`.login-box`, `.nav-btn`, `.camera-box`)
- Kebab-case class names (`.scan-actions`, `.upload-btn`)
- CSS custom properties in `nutrisnap-new/src/index.css` (`:root` with `--text`, `--bg`, etc.)
- Inline styles used occasionally in JSX (`style={{display:"flex", gap:"10px"}}`)
- Color scheme: green-centric (`#7FB77E`, `#5fa764`, `#eaf4ea`, `#f4f8f4`)
### Naming
| Element | Convention | Example |
|---------|-----------|---------|
| Components | PascalCase | `App` |
| CSS classes | kebab-case | `.camera-box`, `.scan-actions` |
| State vars | camelCase | `loggedIn`, `videoRef` |
| Event handlers | camelCase with verb | `handleScan`, `startCamera` |
| Files | PascalCase for components, lowercase for styles | `App.jsx`, `style.css` |

## Git Conventions
- Follow **Conventional Commits** specification.
- Use **Phase IDs** in scopes for project work (e.g., `feat(phase-1): ...`).
- Use **Debug** scope for fixing session issues (e.g., `fix(debug): ...`).
- See detailed standards in `.planning/debug/git-commit-standards.md`.

## Patterns
### State Management
- React `useState` for all state
- `useRef` for DOM references (video element)
- No `useEffect`, no `useContext`, no `useReducer`
- No external state library
### Component Patterns
- **Monolithic component** — all UI in one `App.jsx`
- **Conditional rendering** via early return (`if (!loggedIn) return <Login/>`)
- **Inline event handlers** — no separate handler functions for simple toggles
- **Derived state** — `chartData` computed from `result` in render
### CSS Patterns
- **Dark mode** via CSS class toggle (`.dark` class on wrapper)
- **Float animation** via `@keyframes float`
- **Responsive** via `@media (max-width: 768px)`
- **Gradients** for buttons (`linear-gradient(135deg, #7FB77E, #5fa764)`)
## Error Handling
- No try/catch around `getUserMedia()` (camera access can fail)
- No null checks on file upload (`e.target.files[0]` can be undefined)
- No error boundaries
- No loading states
- No fallback UI
## Key Observations
- Code quality is prototype-level — minimal structure, no error handling
- Inconsistent patterns between root and `nutrisnap-new/` projects
- CSS has competing design systems (Poppins vs Nunito, different index.css variables)
- `nutrisnap-new/src/index.css` has a purple accent (`--accent: #aa3bff`) that conflicts with the green theme in `App.css`
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

## Pattern
## Layers
```
```
## Data Flow
### Root Project (`/`)
```
```
- Pure presentational landing page
- No user interaction beyond hover effects
- External CDN images loaded directly in JSX
### `nutrisnap-new/` Sub-project
```
```
- Login is a simple boolean toggle (no validation, no persistence)
- Dark mode is a CSS class toggle on the wrapper `<div>`
- Food scanning generates random numbers, not actual analysis
- Recharts `BarChart` renders protein/carbs/fat from mock data
## Key Abstractions
- No custom hooks
- No context providers
- No HOCs
- No utility functions
- No shared components
- No constants/config files
## Entry Points
| Project | Entry | Mount |
|---------|-------|-------|
| Root (`/`) | `index.html` → `src/main.jsx` → `App.jsx` | `#root` |
| `nutrisnap-new/` | `index.html` → `src/main.jsx` → `App.jsx` | `#root` |
## Sections in `nutrisnap-new/src/App.jsx`
## Key Observations
- **Two separate, unrelated Vite projects** share the same workspace — unclear which is the "active" one
- `nutrisnap-new/` is a more complete iteration with login, dark mode, scanning, and charts
- Root `/` project is a minimal landing page prototype
- Everything is in one component — no separation of concerns
- Zero testability (no pure functions, no injectable dependencies)
<!-- GSD:architecture-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->



<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
