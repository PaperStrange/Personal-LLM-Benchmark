# Benchmark Admin Dashboard

Admin dashboard for the Personal LLM Benchmark, built on the
[ngx-admin](https://akveo.github.io/ngx-admin/) template (Nebular + Angular 15 + ECharts).

## Pages

- **Overview** (`/pages/dashboard`) — stat cards (100/100 tests green, 3/7 gates,
  2 models looped) plus gate-distribution pie and model-score bar charts.
- **Gates** (`/pages/gates`) — the 7 qualification gates with status and evidence labels.
- **Results** (`/pages/results`) — model run scorecard with `[REAL]/[SIM]/[OPEN]` labels.

## Develop

Requires Node 18 (the template's toolchain predates Node 20+).

```bash
npm install
npx ng serve        # dev server on http://localhost:4200
npx ng build --configuration production   # production build
```

## Data

Dashboard content is driven by `src/app/@core/data/benchmark-data.service.ts`,
which mirrors `results/qualification/` on the `main` branch. Update the service
when new qualification runs land.

The original ngx-admin readme is preserved as `README-ngx-admin.md`.
