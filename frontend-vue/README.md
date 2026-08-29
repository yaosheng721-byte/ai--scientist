# CV AI Scientist Vue Frontend

Vue 3 + Vite + Element Plus frontend for the CV AI Scientist workspace.

## Scripts

```bash
npm install
npm run dev
npm run build
```

The development server proxies `/api` to `http://127.0.0.1:8000`, so the FastAPI service should be started separately:

```bash
uvicorn app.main:app --reload
```

## Structure

```text
src/
  api/              HTTP client and endpoint wrappers
  assets/styles/    global theme and Element Plus overrides
  components/       reusable shell, header, metric, JSON, chart and score UI
  constants/        task module and pool definitions
  router/           route declarations
  stores/           Pinia state for run history and selected run
  utils/            formatting and download helpers
  views/            page-level modules
```
