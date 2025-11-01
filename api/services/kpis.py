"""KPI computation helpers."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from decimal import Decimal
from statistics import mean
from typing import Dict, Iterable, List, Optional

import numpy as np
from sqlalchemy import desc

from ..models import LogEvent, MetricPoint, Service
from ..utils.time import utc_now


def _percentile(values: List[int], percentile: float) -> int:
    if not values:
        return 0
    array = np.array(values)
    return int(round(float(np.percentile(array, percentile))))


def _ensure_decimal(value: float | int) -> Decimal:
    return Decimal(str(round(float(value), 6)))


def refresh_kpis(session, service: Service, config: Dict) -> Optional[dict]:
    """Recompute KPIs for a service over the configured lookback window."""
    lookback = config.get("ALERT_LOOKBACK_MIN", 10)
    window = timedelta(minutes=lookback)
    end = utc_now()
    start = end - window

    logs: List[LogEvent] = (
        session.query(LogEvent)
        .filter(LogEvent.service_id == service.id, LogEvent.ts >= start, LogEvent.ts <= end)
        .order_by(LogEvent.ts.desc())
        .all()
    )
    metrics: List[MetricPoint] = (
        session.query(MetricPoint)
        .filter(MetricPoint.service_id == service.id, MetricPoint.ts >= start, MetricPoint.ts <= end)
        .order_by(MetricPoint.ts.asc())
        .all()
    )

    error_rate = float(metrics[-1].error_rate) if metrics else 0.0
    p95_latency_ms = metrics[-1].p95_latency_ms if metrics else 0
    tps = float(metrics[-1].tps) if metrics else 0.0

    if logs:
        total = len(logs)
        error_count = sum(1 for log in logs if log.level in {"ERROR", "CRITICAL"})
        latency_values = [log.latency_ms for log in logs if log.latency_ms is not None]

        if total > 0:
            error_rate = error_count / total
        if latency_values:
            p95_latency_ms = _percentile(latency_values, 95)
        duration_seconds = max((window.total_seconds()), 1)
        tps = total / duration_seconds

    snapshot = {
        "service": service.name,
        "service_id": service.id,
        "ts": end.isoformat(),
        "error_rate": float(error_rate),
        "p95_latency_ms": int(p95_latency_ms),
        "tps": float(tps),
        "log_count": len(logs),
        "metric_count": len(metrics),
    }

    point = MetricPoint(
        service_id=service.id,
        ts=end,
        error_rate=_ensure_decimal(error_rate),
        p95_latency_ms=int(p95_latency_ms),
        tps=_ensure_decimal(tps),
    )
    session.merge(point)

    return snapshot


def fetch_kpi_series(session, service_name: str, start: datetime, end: datetime) -> dict:
    """Fetch KPI series for charts."""
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
            "error_rate": float(point.error_rate),
            "p95_latency_ms": point.p95_latency_ms,
            "tps": float(point.tps),
        }
        for point in points
    ]

    latest = items[-1] if items else None

    return {
        "service": service_name,
        "range": {"start": start.isoformat(), "end": end.isoformat()},
        "items": items,
        "latest": latest,
    }

