# Testing Strategy

## Backend
- **Tool**: `pytest`.
- **Coverage**: ML pipeline utilities, API endpoints, and database connectors.

## Frontend
- **Tool**: `Vitest` & `React Testing Library`.
- **Coverage**: Component rendering, form logic, and state transitions.

## CI/CD (GitHub Actions)
- **Trigger**: Every push to `main` and all Pull Requests.
- **Jobs**:
  - `lint`: Runs Ruff (backend) and ESLint (frontend).
  - `test`: Runs Pytest and Vitest suites.
  - `build`: Verifies the production build of the frontend.
