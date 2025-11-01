"""Lightweight request validation utilities."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable, List, Optional, Sequence, Tuple

from loguru import logger

VALID_LEVELS = {"DEBUG", "INFO", "WARN", "ERROR", "CRITICAL"}


class SchemaValidationError(Exception):
    """Raised when validation fails."""


@dataclass(slots=True)
class LogRecord:
    service: str
    ts: datetime
    level: str
    message: str
    latency_ms: Optional[int]
    status_code: Optional[int]
    meta: dict


@dataclass(slots=True)
class MetricRecord:
    service: str
    ts: datetime
    tps: float
    error_rate: float
    p95_latency_ms: int


def _ensure_datetime(value: str) -> datetime:
    try:
        if isinstance(value, datetime):
            return value.astimezone(timezone.utc)
        ts = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        return ts.astimezone(timezone.utc)
    except Exception as exc:  # pragma: no cover - defensive
        raise SchemaValidationError(f"Invalid timestamp: {value}") from exc


def validate_log_batch(
    records: Sequence[dict], *, allowlist: Iterable[str] | None = None
) -> Tuple[List[LogRecord], List[dict]]:
    """Validate log payloads, returning (valid, errors)."""
    valid: List[LogRecord] = []
    errors: List[dict] = []
    allow = {svc.strip() for svc in allowlist or [] if svc.strip()}

    if not isinstance(records, Sequence):
        return [], [{"index": None, "error": "Payload must be an array"}]

    for idx, raw in enumerate(records):
        if not isinstance(raw, dict):
            errors.append({"index": idx, "error": "Entry must be an object"})
            continue

        service = str(raw.get("service", "")).strip()
        if not service:
            errors.append({"index": idx, "error": "Missing service"})
            continue
        if allow and service not in allow:
            errors.append({"index": idx, "error": f"Service '{service}' not in allowlist"})
            continue

        level = str(raw.get("level", "")).upper()
        if level not in VALID_LEVELS:
            errors.append({"index": idx, "error": f"Invalid level '{level}'"})
            continue

        message = str(raw.get("message", "")).strip()
        if not message:
            errors.append({"index": idx, "error": "Missing message"})
            continue

        latency = raw.get("latency_ms")
        status_code = raw.get("status_code")
        meta = raw.get("meta") or {}

        try:
            ts = _ensure_datetime(raw.get("ts"))
            latency_val = int(latency) if latency is not None else None
            status_val = int(status_code) if status_code is not None else None
            meta_val = meta if isinstance(meta, dict) else {}
        except Exception as exc:
            logger.debug("Validation error", exc=exc)
            errors.append({"index": idx, "error": "Invalid field types"})
            continue

        valid.append(
            LogRecord(
                service=service,
                ts=ts,
                level=level,
                message=message,
                latency_ms=latency_val,
                status_code=status_val,
                meta=meta_val,
            )
        )

    return valid, errors


def validate_metric_batch(
    records: Sequence[dict], *, allowlist: Iterable[str] | None = None
) -> Tuple[List[MetricRecord], List[dict]]:
    """Validate metric payloads, returning (valid, errors)."""
    valid: List[MetricRecord] = []
    errors: List[dict] = []
    allow = {svc.strip() for svc in allowlist or [] if svc.strip()}

    if not isinstance(records, Sequence):
        return [], [{"index": None, "error": "Payload must be an array"}]

    for idx, raw in enumerate(records):
        if not isinstance(raw, dict):
            errors.append({"index": idx, "error": "Entry must be an object"})
            continue

        service = str(raw.get("service", "")).strip()
        if not service:
            errors.append({"index": idx, "error": "Missing service"})
            continue
        if allow and service not in allow:
            errors.append({"index": idx, "error": f"Service '{service}' not in allowlist"})
            continue

        try:
            ts = _ensure_datetime(raw.get("ts"))
            tps = float(raw.get("tps"))
            error_rate = float(raw.get("error_rate"))
            latency = int(raw.get("p95_latency_ms"))
        except Exception:
            errors.append({"index": idx, "error": "Invalid numeric fields"})
            continue

        valid.append(
            MetricRecord(
                service=service,
                ts=ts,
                tps=tps,
                error_rate=error_rate,
                p95_latency_ms=latency,
            )
        )

    return valid, errors

