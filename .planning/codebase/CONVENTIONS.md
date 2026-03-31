# Development Conventions

## Python / Backend
- **Type Annotations**: Mandatory across all domains (`backend/`, `ai_engine/`, etc.) using the native `typing` definitions.
- **Pydantic Driven**: All payloads going inside and out must conform to explicit Pydantic schemas defined in `backend/schemas/`.
- **Asyncio execution**: All heavy or blocking I/O bound logic should be executed explicitly inside Thread Pools (e.g. `loop.run_in_executor`) to prevent starvation. Route logic should otherwise be `async`.

## TypeScript / Frontend
- **Functional React Components**: Components are written functionally, taking advantage of hooks. No class components.
- **Utility CSS**: Tailwind CSS utility classes are utilized thoroughly within `.tsx` instead of creating standalone style files.
- **Strict Typing**: Axios network requests utilize typed generics and respond via standard interfaces.

## Database
- SQLite is the preferred target; foreign-keys exist reflecting standard normalized SQL relations.
