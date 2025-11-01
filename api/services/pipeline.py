"""Celery tasks for log and metric ingestion."""

from __future__ import annotations

from decimal import Decimal
from typing import Dict, Iterable, List

from loguru import logger
from sqlalchemy.exc import IntegrityError

from ..db import session_scope
from ..models import LogEvent, MetricPoint, Service
from ..schemas import validate_log_batch, validate_metric_batch
from ..services.celery_app import celery
from ..utils.config import load_config
from ..utils.time import utc_now
from . import alerts as alerts_service
from . import anomaly as anomaly_service
from . import kpis as kpi_service


def _ensure_services(session, service_names: Iterable[str]) -> Dict[str, Service]:
    existing = (
        session.query(Service)
        .filter(Service.name.in_(list(service_names)))
        .all()
    )
    mapping = {svc.name: svc for svc in existing}
    for name in service_names:
        if name not in mapping:
            svc = Service(name=name)
            session.add(svc)
            session.flush()
            mapping[name] = svc
    return mapping


@celery.task(name="flowguard.parse_logs")
def parse_logs_task(payload: List[dict]) -> dict:
    config = load_config()
    records, errors = validate_log_batch(payload, allowlist=config["SERVICE_ALLOWLIST"])
    if not records:
        logger.warning("All log records invalid", errors=errors)
        return {"status": "skipped", "errors": errors}

    with session_scope() as session:
        services = _ensure_services(session, {record.service for record in records})
        inserted = 0
        for record in records:
            service = services[record.service]
            event = LogEvent(
                service_id=service.id,
                ts=record.ts,
                level=record.level,
                message=record.message,
                latency_ms=record.latency_ms,
                status_code=record.status_code,
                meta=record.meta,
            )
            session.add(event)
            inserted += 1

        session.flush()

        snapshots = []
        for service in services.values():
            snapshot = kpi_service.refresh_kpis(session, service, config)
            if snapshot:
                anomaly = anomaly_service.evaluate(service.name, snapshot, config)
                alerts_service.handle_alerts(session, service, snapshot, anomaly, config)
                snapshots.append({**snapshot, "anomaly": anomaly})

    logger.info("Processed log batch", inserted=inserted, services=len(services))
    return {"status": "ok", "inserted": inserted, "errors": errors, "snapshots": snapshots}


@celery.task(name="flowguard.aggregate_metrics")
def aggregate_metrics_task(payload: List[dict]) -> dict:
    config = load_config()
    records, errors = validate_metric_batch(payload, allowlist=config["SERVICE_ALLOWLIST"])
    if not records:
        logger.warning("All metric records invalid", errors=errors)
        return {"status": "skipped", "errors": errors}

    with session_scope() as session:
        services = _ensure_services(session, {record.service for record in records})
        upserted = 0
        for record in records:
            service = services[record.service]
            point = MetricPoint(
                service_id=service.id,
                ts=record.ts,
                tps=Decimal(str(round(record.tps, 6))),
                error_rate=Decimal(str(round(record.error_rate, 6))),
                p95_latency_ms=record.p95_latency_ms,
            )
            try:
                session.merge(point)
            except IntegrityError:
                session.rollback()
                session.merge(point)
            upserted += 1

        snapshots = []
        for service in services.values():
            snapshot = kpi_service.refresh_kpis(session, service, config)
            if snapshot:
                anomaly = anomaly_service.evaluate(service.name, snapshot, config)
                alerts_service.handle_alerts(session, service, snapshot, anomaly, config)
                snapshots.append({**snapshot, "anomaly": anomaly})

    logger.info("Processed metric batch", count=upserted, services=len(services))
    return {"status": "ok", "upserted": upserted, "errors": errors, "snapshots": snapshots}
