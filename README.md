# FlowGuard – Intelligent Log & Metrics Aggregator
<img width="1576" height="935" alt="flowguard_dashboard" src="https://github.com/user-attachments/assets/4c379421-d0dc-4473-909e-d3d9284d0d3e" />

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

## Screenshots
Screenshot 1
<img width="1576" height="935" alt="flowguard_dashboard" src="https://github.com/user-attachments/assets/66b4c674-7059-4623-861c-55737ddab1d2" />
1. Dashboard Overview
Unified KPIs and performance charts for error rate, latency, and throughput.
Monitor real-time trends across services with interactive charts and anomaly highlights powered by IsolationForest detection.

Screenshot 2
<img width="1578" height="935" alt="flowguard_explore" src="https://github.com/user-attachments/assets/38edd5e4-d174-4b54-b361-44ab6c28a831" />
2. Explorer Screen
Search and filter logs by service, severity, or message content.
Navigate high-volume log data efficiently with virtualized tables and color-coded severity levels for quick triage.

Screenshot 3
<img width="1580" height="933" alt="flowguard_settings" src="https://github.com/user-attachments/assets/a2149246-309b-4f05-b6cb-c247127abb67" />
3. Settings Panel
View system configuration and trigger test alerts.
Displays live configuration values (thresholds, alert channels, and allowlisted services) and allows one-click Slack or email test alerts.

## Next steps

- Configure production Postgres (`DB_URL=postgresql+psycopg://user:pass@host/db`)
- Supply Slack webhook and SMTP credentials for alerting
- Deploy with CI/CD (build Docker images from `api/` and `web/`)

