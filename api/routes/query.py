"""Query endpoints for logs and metrics."""

from __future__ import annotations

from flask import Blueprint, jsonify, request
from sqlalchemy import and_, func

from api.db import session_scope
from api.models import AlertEvent, LogEvent, MetricPoint, Service
from api.services.kpis import fetch_kpi_series
from api.utils.time import parse_range

bp = Blueprint("query", __name__, url_prefix="/api")


@bp.get("/logs")
def get_logs() -> tuple[dict, int]:
    service_name = request.args.get("service")
    level = request.args.get("level")
    query_text = request.args.get("q")
    range_value = request.args.get("range", "1h")
    start, end = parse_range(range_value)

    with session_scope() as session:
        q = session.query(LogEvent, Service.name).join(Service)
        if service_name:
            q = q.filter(Service.name == service_name)
        if level:
            q = q.filter(LogEvent.level == level.upper())
        if query_text:
            q = q.filter(LogEvent.message.ilike(f"%{query_text}%"))
        q = q.filter(and_(LogEvent.ts >= start, LogEvent.ts <= end))
        q = q.order_by(LogEvent.ts.desc()).limit(500)

        results = [
            {
                "id": log.id,
                "service": svc_name,
                "ts": log.ts.isoformat(),
                "level": log.level,
                "message": log.message,
                "latency_ms": log.latency_ms,
                "status_code": log.status_code,
                "meta": log.meta or {},
            }
            for log, svc_name in q.all()
        ]

    return jsonify({"items": results}), 200


@bp.get("/metrics")
def get_metrics() -> tuple[dict, int]:
    service_name = request.args.get("service")
    if not service_name:
        return jsonify({"status": "error", "message": "service query parameter required"}), 400

    range_value = request.args.get("range", "1h")
    start, end = parse_range(range_value)

    with session_scope() as session:
        points = (
            session.query(MetricPoint)
            .join(Service)
            .filter(
                Service.name == service_name,
                MetricPoint.ts >= start,
                MetricPoint.ts <= end,
            )
            .order_by(MetricPoint.ts.asc())
            .all()
        )

        items = [
            {
                "ts": point.ts.isoformat(),
                "tps": float(point.tps),
                "error_rate": float(point.error_rate),
                "p95_latency_ms": point.p95_latency_ms,
            }
            for point in points
        ]

    return jsonify({"service": service_name, "items": items}), 200


@bp.get("/kpis")
def get_kpis() -> tuple[dict, int]:
    service_name = request.args.get("service")
    if not service_name:
        return jsonify({"status": "error", "message": "service query parameter required"}), 400

    range_value = request.args.get("range", "1h")
    start, end = parse_range(range_value)

    with session_scope() as session:
        data = fetch_kpi_series(session, service_name, start, end)

    return jsonify(data), 200


@bp.get("/alerts")
def get_alerts() -> tuple[dict, int]:
    limit = int(request.args.get("limit", 50))

    with session_scope() as session:
        rows = (
            session.query(AlertEvent, Service.name)
            .join(Service)
            .order_by(AlertEvent.ts.desc())
            .limit(limit)
            .all()
        )

        items = [
            {
                "id": alert.id,
                "service": svc,
                "channel": alert.channel,
                "severity": alert.severity,
                "message": alert.message,
                "ts": alert.ts.isoformat(),
            }
            for alert, svc in rows
        ]

    return jsonify({"items": items}), 200
