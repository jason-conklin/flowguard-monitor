# FlowGuard Web UI

React + Vite single-page dashboard for FlowGuard. It surfaces live KPIs, charts, log exploration, and configuration.

## Stack

- React 18 with Vite dev server
- React Router for navigation
- Axios for REST calls
- Chart.js via `react-chartjs-2` for KPI visualisation
- `react-window` for virtualised log table rendering

## Getting started

```bash
cd web
npm install
VITE_API_BASE=http://localhost:8000 npm run dev
```

The app runs on http://localhost:5173.

For production build:

```bash
npm run build
npm run preview
```

Ensure the backend Flask API is running and accessible at `VITE_API_BASE`.

## Features

- Dashboard with KPI tiles, charts, and alert timeline
- Explorer for filtering logs by service, level, range, and search terms
- Settings screen exposing runtime configuration and a “Send Test Alert” action
- Responsive layout with lightweight styling (no CSS frameworks)

