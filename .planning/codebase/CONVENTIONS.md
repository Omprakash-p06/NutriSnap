# Code Conventions

## Backend (Python)
- **Style**: PEP 8 compliance.
- **Linting**: Ruff for fast linting and formatting.
- **Type Hinting**: Mandatory for all function signatures.
- **Docs**: Google-style docstrings.

## Frontend (JS/React)
- **Framework**: Functional components with Hooks.
- **Linting**: ESLint + Prettier.
- **State**: React Context for global state, local hooks for UI state.

## Git & Workflow
- **Commits**: Semantic commits (e.g., `feat:`, `fix:`, `docs:`).
- **Branching**: Feature branches merged via Pull Request.
- **Debug Sessions**: Always propose a commit with a descriptive message after a debug session (triggered via `/gsd:debug`) is completed and resolved.
- **CI Synchronization**: Ensure GitHub workflow files are synchronized with the project structure (e.g., paths, dependencies) and that all tests pass before completing tasks.
