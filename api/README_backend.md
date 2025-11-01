# FlowGuard API

FlowGuard is an intelligent log and metrics aggregator designed to ingest events from multiple services, classify and tag their severity, compute key performance indicators, perform anomaly detection, and trigger alerts. This document covers the backend stack and day-to-day operations.

## Features
- Flask API with CORS enabled (`/api/*` namespace)
- SQLAlchemy ORM models for services, logs, metrics, and alert history
- Celery workers backed by Redis for asynchronous ingestion and processing
- KPI computation (error rate, p95 latency, throughput) with anomaly detection (IsolationForest fallback to z-score)
- Slack webhook and SMTP email alerting with deduplication
- Optional development generator that streams synthetic traffic to the API

## Requirements
- Python 3.10+
- Redis (local or via Docker)
- PostgreSQL (production) or SQLite (default development)

Install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Copy the environment template and adjust values for your environment:

```bash
cp .env.example .env
```

## Running locally

```bash
export FLASK_APP=app.py
python app.py  # API on http://localhost:8000
```

In a separate terminal, start Celery:

```bash
celery -A services.celery_app.celery worker --loglevel=INFO
```

Enable the synthetic generator (optional, controlled by `DEV_GENERATOR=true`) to populate dashboards:

```bash
python -m collectors.demo_generator
```

## API quickstart

### Health
```bash
curl http://localhost:8000/api/health
```

### Ingest logs
```bash
curl -X POST http://localhost:8000/api/ingest/logs \
  -H "Content-Type: application/json" \
  -d '[{
        "service": "auth",
        "ts": "2024-01-01T12:00:00Z",
        "level": "ERROR",
        "message": "Auth failed latency=850ms status=500",
        "latency_ms": 850,
        "status_code": 500
      }]'
```

### Ingest metrics
```bash
curl -X POST http://localhost:8000/api/ingest/metrics \
  -H "Content-Type: application/json" \
  -d '[{
        "service": "auth",
        "ts": "2024-01-01T12:00:00Z",
        "tps": 28.5,
        "error_rate": 0.08,
        "p95_latency_ms": 650
      }]'
```

### Query endpoints
```bash
curl "http://localhost:8000/api/logs?service=auth&range=1h"
curl "http://localhost:8000/api/metrics?service=auth&range=24h"
curl "http://localhost:8000/api/kpis?service=auth&range=1h"
curl "http://localhost:8000/api/alerts?limit=20"
curl "http://localhost:8000/api/config"
```

### Trigger test alert
```bash
curl -X POST http://localhost:8000/api/test-alert \
  -H "Content-Type: application/json" \
  -d '{"service": "auth"}'
```

## Notes
- `services/pipeline.py` is the central ingestion pipeline for logs and metrics. It validates payloads, persists data, recomputes KPIs, performs anomaly checks, and issues alerts.
- Alert deduplication uses `service:reason:window` keys; adjust the window with `FLOWGUARD_ALERT_WINDOW_MIN`.
- For production deployments, run behind Gunicorn (see `docker-compose.yml` at the project root once generated).

