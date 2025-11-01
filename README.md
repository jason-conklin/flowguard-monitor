# FlowGuard – Intelligent Log & Metrics Aggregator

FlowGuard ingests logs and metrics from distributed services, classifies and tags their severity, aggregates KPIs (error rate, p95 latency, throughput), detects anomalies, stores everything for querying, and surfaces alerts alongside a rich dashboard.

## Stack

- **Backend:** Python 3.10+, Flask, SQLAlchemy, Celery + Redis, IsolationForest (scikit-learn), loguru
- **Frontend:** React + Vite, Axios, Chart.js (`react-chartjs-2`)
- **Alerts:** Slack webhook + SMTP email
- **Packaging:** Docker Compose (API, Celery worker, Redis, Web)

## Project layout

```
flowguard/
├── api/                # Flask backend, Celery pipeline, collectors
├── web/                # React dashboard
├── docker-compose.yml  # Orchestrated deployment
└── README.md           # (this file)
```

## Local development

Prerequisites: Python 3.10+, Node 18+, Redis (e.g. via Docker). SQLite is used by default; configure PostgreSQL via `DB_URL` when ready.

1. **Backend**
   ```bash
   cd api
   python -m venv .venv
   # Windows: .venv\Scripts\activate
   # Unix/macOS:
   source .venv/bin/activate
   pip install -r requirements.txt
   cp .env.example .env
   python app.py  # Runs Flask on http://localhost:8000
   ```

2. **Celery worker**
   ```bash
   # From the api directory with the virtualenv activated
   celery -A services.celery_app.celery worker --loglevel=INFO
   ```

3. **Frontend**
   ```bash
   cd ../web
   npm install
   VITE_API_BASE=http://localhost:8000 npm run dev  # Vite on http://localhost:5173
   ```

Visit http://localhost:5173 to explore the dashboard.

## Docker workflow

The provided Compose file bundles the API, worker, Redis, and web UI.

```bash
docker-compose up --build
```

Services:
- `api`: Gunicorn-served Flask API on port 8000
- `worker`: Celery worker consuming ingestion tasks
- `redis`: Message broker / result backend
- `web`: Nginx-hosted static dashboard on port 8080

Set environment overrides via `.env` files in `api/` before building, or docker-compose environment variables.

## Synthetic data generator

With `DEV_GENERATOR=true` in `api/.env`, run:

```bash
cd api
python -m collectors.demo_generator
```

This streams synthetic logs and metrics into the local API, populating the dashboard for demos.

## Key endpoints

- `GET /api/health` – service probe
- `POST /api/ingest/logs` – enqueue log batch
- `POST /api/ingest/metrics` – enqueue metric batch
- `GET /api/logs` – filter/query log events
- `GET /api/metrics` – fetch aggregated points
- `GET /api/kpis` – chart-ready KPIs
- `GET /api/alerts` – recent alerts
- `POST /api/test-alert` – send synthetic alert across configured channels

## Next steps

- Configure production Postgres (`DB_URL=postgresql+psycopg://user:pass@host/db`)
- Supply Slack webhook and SMTP credentials for alerting
- Deploy with CI/CD (build Docker images from `api/` and `web/`)

