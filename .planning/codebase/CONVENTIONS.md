# Coding Conventions

**Refresh Date:** 2026-04-27

## General Principles
- **Clarity over Conciseness:** Write readable code that self-documents its intent.
- **Fail Early:** Use aggressive validation for inputs (pydantic in backend, prop-types/typescript-like patterns in frontend).

## Backend (Python)
- **Style:** Adhere to PEP 8.
- **Formatting:** Use Black (88 chars).
- **Naming:**
  - Classes: `PascalCase`.
  - Functions/Variables: `snake_case`.
  - Constants: `UPPER_SNAKE_CASE`.
- **Type Hinting:** Mandatory for all function signatures using Python 3.10 syntax (e.g., `str | None`).
- **Async:** Use `async/await` for all I/O bound operations (API routes, DB calls).
- **Imports:** Absolute imports preferred (`from nutrisnap.utils import ...`).

## Frontend (React/JS)
- **Style:** Modern functional components with Hooks.
- **Naming:**
  - Components: `PascalCase` (`AuthModal.jsx`).
  - Hooks: `camelCase` starting with `use` (`useAuth.js`).
  - CSS: Modular CSS preferred, or consistent class naming for global styles.
- **Animations:** Prefer `framer-motion` over raw CSS transitions for complex interactions.
- **State:** Use local state (`useState`) for UI logic; use Context for global state (Auth, Theme).

## API Design
- **RESTful:** Use standard HTTP verbs (GET, POST, PUT, DELETE).
- **Versioning:** (Planned) `/api/v1/...`.
- **Error Responses:** Consistent JSON structure: `{"error": "string", "detail": {...}}`.

## Git & Workflow
- **Commit Messages:** Imperative mood (`Add segmentation stage`, not `Added...`).
- **Branching:** Short-lived feature branches.
- **GSD Integration:** Maintain `.planning/` directory for task tracking and architecture state.
