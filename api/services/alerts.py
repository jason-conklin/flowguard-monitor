"""Alert dispatching for FlowGuard."""

from __future__ import annotations

import json
import smtplib
from collections import defaultdict
from datetime import timedelta
from email.message import EmailMessage
from typing import Dict, Iterable, List, Optional
from urllib import request as urlrequest

from loguru import logger
from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError

from api.models import AlertEvent, Service
from api.utils.time import utc_now


def handle_alerts(session, service: Service, snapshot: dict, anomaly: dict, config: dict) -> List[dict]:
    """Check thresholds and anomalies and dispatch alerts if needed."""
    threshold_error_rate = config.get("ALERT_ERROR_RATE_THRESHOLD", 0.05)
    threshold_latency = config.get("ALERT_P95_LATENCY_MS", 500)
    window_min = config.get("FLOWGUARD_ALERT_WINDOW_MIN", 10)
    channels = config.get("ALERT_CHANNELS", [])

    triggers: List[dict] = []

    if snapshot["error_rate"] >= threshold_error_rate:
        severity = "critical" if snapshot["error_rate"] >= threshold_error_rate * 2 else "warn"
        triggers.append(
            {
                "reason": "error_rate_threshold",
                "severity": severity,
                "message": f"Error rate {snapshot['error_rate']:.2%} exceeded threshold",
            }
        )

    if snapshot["p95_latency_ms"] >= threshold_latency:
        severity = "critical" if snapshot["p95_latency_ms"] >= threshold_latency * 1.5 else "warn"
        triggers.append(
            {
                "reason": "latency_threshold",
                "severity": severity,
                "message": f"p95 latency {snapshot['p95_latency_ms']}ms exceeded threshold",
            }
        )

    if anomaly.get("is_anomaly"):
        triggers.append(
            {
                "reason": "anomaly_detected",
                "severity": "warn",
                "message": anomaly.get("reason", "Anomaly detected"),
            }
        )

    dispatched: List[dict] = []
    if not triggers:
        return dispatched

    for trigger in triggers:
        dedupe_key = f"{service.name}:{trigger['reason']}:{snapshot['ts'][:16]}"
        if _is_duplicate(session, service.id, dedupe_key, window_min):
            continue
        for channel in channels:
            if _dispatch_channel(channel, service, snapshot, trigger, config):
                alert = AlertEvent(
                    service_id=service.id,
                    ts=utc_now(),
                    channel=channel,
                    severity=trigger["severity"],
                    message=trigger["message"],
                    dedupe_key=dedupe_key,
                )
                session.add(alert)
                dispatched.append(
                    {
                        "channel": channel,
                        "severity": trigger["severity"],
                        "message": trigger["message"],
                    }
                )

    try:
        session.flush()
    except IntegrityError:  # pragma: no cover - dedupe floor
        session.rollback()

    return dispatched


def dispatch_test_alert(session, config: dict, service_name: Optional[str] = None) -> dict:
    """Send a test alert across configured channels."""
    service_label = service_name or "demo"
    service = (
        session.query(Service).filter(Service.name == service_label).one_or_none()
        if service_name
        else None
    )
    if service is None:
        service = Service(name=service_label)
        session.merge(service)
        session.flush()

    snapshot = {
        "service": service.name,
        "ts": utc_now().isoformat(),
        "error_rate": float(config.get("ALERT_ERROR_RATE_THRESHOLD", 0.05)) * 1.2,
        "p95_latency_ms": int(config.get("ALERT_P95_LATENCY_MS", 500) * 1.1),
        "tps": 0.0,
    }
    anomaly = {"is_anomaly": True, "reason": "Test alert"}
    dispatched = handle_alerts(session, service, snapshot, anomaly, config)

    return {"status": "accepted", "dispatched": dispatched}


def _dispatch_channel(channel: str, service: Service, snapshot: dict, trigger: dict, config: dict) -> bool:
    channel = channel.lower()
    if channel == "slack":
        return _send_slack(service, snapshot, trigger, config)
    if channel == "email":
        return _send_email(service, snapshot, trigger, config)
    logger.warning("Unsupported alert channel", channel=channel)
    return False


def _send_slack(service: Service, snapshot: dict, trigger: dict, config: dict) -> bool:
    webhook = config.get("SLACK_WEBHOOK_URL")
    if not webhook:
        logger.debug("Slack webhook not configured; skipping alert")
        return False

    payload = {
        "text": (
            f"*FlowGuard alert* for `{service.name}`\\n"
            f"{trigger['message']}\\n"
            f"Error rate: {snapshot['error_rate']:.2%}, "
            f"p95 latency: {snapshot['p95_latency_ms']}ms, "
            f"TPS: {snapshot['tps']:.2f}"
        )
    }
    try:
        req = urlrequest.Request(
            webhook, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"}
        )
        with urlrequest.urlopen(req, timeout=5) as resp:
            return 200 <= resp.status < 300
    except Exception as exc:  # pragma: no cover - IO
        logger.warning("Slack alert failed", error=str(exc))
        return False


def _send_email(service: Service, snapshot: dict, trigger: dict, config: dict) -> bool:
    host = config.get("SMTP_HOST")
    user = config.get("SMTP_USER")
    password = config.get("SMTP_PASS")
    to_addr = config.get("SMTP_TO")
    from_addr = config.get("SMTP_FROM")

    if not all([host, user, password, to_addr, from_addr]):
        logger.debug("Email alert not fully configured; skipping")
        return False

    subject = f"FlowGuard alert: {service.name}"
    body = (
        f"Service: {service.name}\\n"
        f"Reason: {trigger['message']}\\n"
        f"Error rate: {snapshot['error_rate']:.2%}\\n"
        f"p95 latency: {snapshot['p95_latency_ms']}ms\\n"
        f"TPS: {snapshot['tps']:.2f}\\n"
    )

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = from_addr
    message["To"] = to_addr
    message.set_content(body)

    try:
        with smtplib.SMTP(host, config.get("SMTP_PORT", 587)) as smtp:
            smtp.starttls()
            smtp.login(user, password)
            smtp.send_message(message)
        return True
    except Exception as exc:  # pragma: no cover - IO
        logger.warning("Email alert failed", error=str(exc))
        return False


def _is_duplicate(session, service_id: int, dedupe_key: str, window_min: int) -> bool:
    cutoff = utc_now() - timedelta(minutes=window_min)
    exists = (
        session.query(AlertEvent)
        .filter(
            AlertEvent.service_id == service_id,
            AlertEvent.dedupe_key == dedupe_key,
            AlertEvent.ts >= cutoff,
        )
        .first()
    )
    return exists is not None
