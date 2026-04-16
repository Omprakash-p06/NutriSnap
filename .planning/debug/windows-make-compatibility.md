---
status: resolved
trigger: "'make' is not recognized as an internal or external command on Windows"
symptoms:
  expected: "Makefile targets run successfully."
  actual: "Command fails with 'not recognized' error."
  error_messages: "'make' is not recognized..."
  timeline: "Initial setup on Windows."
  reproduction: "make setup-data"
created: 2026-04-15
updated: 2026-04-15
---

# Windows 'make' Compatibility Issue

## Root Cause
The `make` utility is not a native Windows command. The project uses a `Makefile` for shortcuts, assuming a Unix-like environment or the presence of GNU Make.

## Resolution
- Provided the direct Python command for Windows: `.venv\Scripts\python scripts/setup_dataset.py`.
- Updated `README.md` with Windows-specific execution instructions for key targets.

## Verification
- User can run scripts directly using `.venv\Scripts\python`.
