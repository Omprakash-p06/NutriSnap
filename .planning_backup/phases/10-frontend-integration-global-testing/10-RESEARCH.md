# Phase 10: Frontend Integration & Global Testing - Research

**Researched:** 2026-04-26
**Domain:** React/FastAPI Integration, E2E Testing, Performance Benchmarking
**Confidence:** HIGH

## Summary

This research establishes the blueprint for integrating the NutriSnap FastAPI backend with a modern React 19 frontend. The primary challenge is coordinating long-running AI inference tasks (image processing, SAM 2, GLPN, ViT) with a responsive user interface. We recommend a "Polling with Progress" pattern and a robust E2E testing strategy using Playwright that accounts for AI latency and non-determinism.

**Primary recommendation:** Use a Vite-based development proxy to eliminate CORS issues locally and implement Axios interceptors for seamless JWT authentication management.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| React | 19.2.0 | Frontend UI | Decided (CLAUDE.md); supports new `use` and Actions primitives. |
| Vite | 7.3.0 | Build Tool | Standard for modern React; provides fast HMR and proxy support. |
| Axios | 1.7.9 | API Client | Decided (CLAUDE.md); supports interceptors for JWT injection. |
| Tailwind CSS | 4.0.0 | Styling | Utility-first styling for rapid UI development. |
| Lucide React | 0.474.0 | Icons | Lightweight, consistent icon set. |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|--------------|
| Playwright | 1.50.0 | E2E Testing | Core journey testing; superior to Cypress for modern React. |
| Zod | 3.24.1 | Schema Validation | Client-side validation mirroring Pydantic models. |
| React Hook Form | 7.54.2 | Form Management | Handling login, registration, and meal logs. |
| k6 | 0.57.0 | Load Testing | Benchmarking backend under concurrent user load. |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Axios | Native Fetch | Fetch lacks interceptors and requires more boilerplate for error handling. |
| Playwright | Cypress | Cypress is slower and has more trouble with modern Vite/ESM setups. |
| Local State | TanStack Query | While TanStack Query is excellent, the project constraint prefers local state + axios. |

**Installation:**
```bash
# Frontend initialization (if directory is empty)
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install axios lucide-react react-hook-form zod tailwindcss @tailwindcss/vite
# Testing
npm install -D @playwright/test
```

## Architecture Patterns

### Recommended Project Structure
```
frontend/
├── public/          # Static assets
├── src/
│   ├── api/         # Axios client and endpoint wrappers
│   ├── components/  # Reusable UI (Button, Card, Modal)
│   ├── hooks/       # Custom hooks (useAuth, usePrediction)
│   ├── pages/       # Route components (Dashboard, Login, Upload)
│   ├── types/       # TypeScript interfaces (matching schemas.py)
│   ├── App.tsx      # Main routing and layout
│   └── main.tsx     # Entry point
├── tests/           # E2E tests (Playwright)
├── vite.config.ts   # Proxy configuration
└── tailwind.config.ts
```

### Pattern 1: Vite Proxy (CORS-free Dev)
**What:** Proxy `/api` requests to `http://localhost:8000`.
**When to use:** Local development to avoid CORS errors and simplify URL management.
**Example:**
```typescript
// frontend/vite.config.ts
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
})
```

### Pattern 2: Axios Interceptors (Auth Plumbing)
**What:** Automatically attach JWT to every request and handle 401s globally.
**Example:**
```typescript
// frontend/src/api/client.ts
const api = axios.create({ baseURL: '/api' });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(err);
  }
);
```

### Pattern 3: Polling for AI Results
**What:** Non-blocking upload followed by status polling.
**Example:**
```typescript
// frontend/src/hooks/usePrediction.ts
const pollResult = async (imageId: string) => {
  const res = await api.get(`/result/${imageId}`);
  if (res.data.status === 'completed') return res.data;
  if (res.data.status === 'failed') throw new Error('AI failed');
  await new Promise(r => setTimeout(r, 1000));
  return pollResult(imageId);
};
```

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Auth State | Custom Context | `useAuth` hook + LocalStorage | Simplifies token persistence and access. |
| Form Validation | Regex / Manual | `Zod` + `react-hook-form` | Handles complex errors and types automatically. |
| Polling | Custom `setInterval` | Recursive `setTimeout` or `useEffect` | Avoids interval overlap and memory leaks. |
| Image Preview | Server-side upload | `URL.createObjectURL(file)` | Instant UX feedback before upload. |

## Common Pitfalls

### Pitfall 1: VRAM Exhaustion in E2E Tests
**What goes wrong:** Parallel Playwright workers trigger multiple `POST /predict` calls, crashing the 4GB GPU.
**How to avoid:** Limit Playwright workers to 1 for AI-intensive tests or use a "Mock AI" mode that returns fixed results.

### Pitfall 2: Token Expiry during Long Polling
**What goes wrong:** Access token expires while waiting for a 15-second AI process.
**How to avoid:** Ensure `ACCESS_TOKEN_EXPIRE_MINUTES` is at least 30, and the frontend handles retry-after-refresh if possible.

### Pitfall 3: Large File Uploads
**What goes wrong:** Users upload 20MB 4K photos, causing request timeouts and slow processing.
**How to avoid:** Implement client-side image resizing/compression using a canvas or library before upload.

## Code Examples

### Integrated Prediction Flow
```typescript
// frontend/src/pages/Upload.tsx
const handleUpload = async (file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  
  // 1. Trigger
  const { data: { image_id } } = await api.post('/predict', formData);
  
  // 2. Poll (UI shows loading)
  const result = await pollResult(image_id);
  
  // 3. Display
  setNutrition(result.nutrition);
};
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `useEffect` fetching | React 19 `use(promise)` | 2024 | Cleaner component code, built-in Suspense. |
| Manual Error States | `useActionState` | 2024 | Native transition handling for forms. |
| Cypress | Playwright | 2023 | 2-3x faster tests, better trace debugging. |

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Node.js | Frontend Dev/Build | ✓ | 24.11.1 | — |
| npm | Package Management | ✓ | 11.6.2 | — |
| Playwright | E2E Testing | ✓ | 1.59.1 | — |
| Backend API | Integration | ✓ | localhost:8000 | Mock API |

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | Playwright |
| Config file | `frontend/playwright.config.ts` |
| Quick run command | `npx playwright test` |
| Full suite command | `npx playwright test --project=chromium --headed` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| FE-01 | Login & JWT Persistence | E2E | `npx playwright test tests/auth.spec.ts` | ❌ Wave 0 |
| FE-02 | Image Upload & Polling | E2E | `npx playwright test tests/predict.spec.ts` | ❌ Wave 0 |
| FE-03 | USDA Search & Logging | E2E | `npx playwright test tests/logs.spec.ts` | ❌ Wave 0 |
| PERF-01 | < 200ms API response | Load | `k6 run tests/load/api.js` | ❌ Wave 0 |

### Wave 0 Gaps
- [ ] `frontend/` initialization (if not present)
- [ ] `playwright.config.ts` setup
- [ ] `tests/fixtures/sample_meal.jpg` for upload tests

## Sources

### Primary (HIGH confidence)
- Official React 19 Docs - Actions and `use` hook.
- Vite Official Guide - Backend Proxying.
- Playwright Documentation - File upload and polling (`expect.poll`).

### Secondary (MEDIUM confidence)
- Grafana k6 docs - API benchmarking.
- Google Lighthouse - Core Web Vitals targets.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Directly follows CLAUDE.md and current best practices.
- Architecture: HIGH - Standard Proxy/Interceptors/Polling pattern.
- Pitfalls: MEDIUM - Based on common AI/FastAPI integration issues.

**Research date:** 2026-04-26
**Valid until:** 2026-07-26
