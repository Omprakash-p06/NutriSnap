# Debug Session: missing-dependency-email-validator

## Symptoms
- **Actual behavior**: Backend crashes on startup with `ImportError`.
- **Error message**: `ImportError: email-validator is not installed, run pip install 'pydantic[email]'`
- **Timeline**: Started after running backend on port 5000.

## Hypotheses
1. **Missing dependency**: `email-validator` is used by Pydantic (likely in `schemas.py` for `EmailStr`) but not listed in `requirements.txt`.

## Investigation
- Checked `backend/app/schemas.py`. It likely uses `EmailStr`.
- Checked `backend/requirements.txt`.

## Root Cause
`email-validator` is missing from `requirements.txt`.

## Fix
Add `email-validator` to `backend/requirements.txt`.

## Verification
1. `pip install email-validator`
2. `uvicorn app.main:app --reload --port 5000`
