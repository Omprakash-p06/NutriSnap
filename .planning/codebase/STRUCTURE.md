# Project Structure

```text
/
├── backend/            # Python FastAPI & ML logic
│   ├── app/            # API routers, models, and services
│   ├── nutrisnap/      # Core ML inference package
│   ├── models/         # Model weights (.pth, .pt)
│   ├── data/           # CSV/JSON databases
│   └── tests/          # Pytest suite
├── frontend/           # Vite + React PWA
│   ├── src/            # React source (components, hooks, pages)
│   ├── public/         # Static assets and manifest
│   └── package.json
├── .github/            # CI/CD workflows
└── .planning/          # Documentation and mapping
```
