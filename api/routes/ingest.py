"""Ingestion endpoints for logs and metrics."""

from __future__ import annotations

from flask import Blueprint, current_app, jsonify, request
from loguru import logger

from ..schemas import LogRecord, MetricRecord, validate_log_batch, validate_metric_batch
from ..services.pipeline import aggregate_metrics_task, parse_logs_task

bp = Blueprint("ingest", __name__, url_prefix="/api")


def _serialize_log(record: LogRecord) -> dict:
    return {
        "service": record.service,
        "ts": record.ts.isoformat(),
        "level": record.level,
        "message": record.message,
        "latency_ms": record.latency_ms,
        "status_code": record.status_code,
        "meta": record.meta,
    }


def _serialize_metric(record: MetricRecord) -> dict:
    return {
        "service": record.service,
        "ts": record.ts.isoformat(),
        "tps": record.tps,
        "error_rate": record.error_rate,
        "p95_latency_ms": record.p95_latency_ms,
    }


@bp.post("/ingest/logs")
def ingest_logs() -> tuple[dict, int]:
    payload = request.get_json(force=True, silent=True)
    if payload is None:
        return jsonify({"status": "error", "message": "Invalid JSON"}), 400

    allowlist = current_app.config.get("SERVICE_ALLOWLIST", [])
    records, errors = validate_log_batch(payload, allowlist=allowlist)
    if not records:
        return jsonify({"status": "error", "errors": errors}), 400

    serialized = [_serialize_log(record) for record in records]
    task = parse_logs_task.delay(serialized)
    logger.bind(component="api.ingest").info(
        "Queued log ingestion batch", count=len(serialized), task_id=task.id
    )
    return (
        jsonify(
            {
                "status": "accepted",
                "task_id": task.id,
                "accepted": len(serialized),
                "errors": errors,
            }
        ),
        202,
    )


@bp.post("/ingest/metrics")
def ingest_metrics() -> tuple[dict, int]:
    payload = request.get_json(force=True, silent=True)
    if payload is None:
        return jsonify({"status": "error", "message": "Invalid JSON"}), 400

    allowlist = current_app.config.get("SERVICE_ALLOWLIST", [])
    records, errors = validate_metric_batch(payload, allowlist=allowlist)
    if not records:
        return jsonify({"status": "error", "errors": errors}), 400

    serialized = [_serialize_metric(record) for record in records]
    task = aggregate_metrics_task.delay(serialized)
    logger.bind(component="api.ingest").info(
        "Queued metric ingestion batch", count=len(serialized), task_id=task.id
    )
    return (
        jsonify(
            {
                "status": "accepted",
                "task_id": task.id,
                "accepted": len(serialized),
                "errors": errors,
            }
        ),
        202,
    )

