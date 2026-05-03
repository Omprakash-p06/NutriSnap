# Git Commit Standards for Debug Sessions

## Process Standard: Post-Debug Commit
- **Standard:** After every debug session (triggered via `/gsd:debug`) is completed and resolved, the agent MUST propose a commit to persist the fixes.
- **Verification:** Before proposing a commit, ensure that GitHub workflow files are synchronized with the project structure and that all relevant tests pass.
- **Commit Style:** Use the `fix(debug):` scope for these commits.
- **Message Content:** Briefly summarize the root cause and the fix applied.

## General Git Conventions
- Follow **Conventional Commits** specification.
- Use **Phase IDs** in scopes for project work (e.g., `feat(phase-1): ...`).
- Use **Debug** scope for fixing session issues (e.g., `fix(debug): ...`).
