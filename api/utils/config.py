"""Environment and configuration helpers."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Iterable, List

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_ENV_PATH = BASE_DIR / ".env"

DEFAULTS: Dict[str, Any] = {
    "DB_URL": "sqlite:///flowguard.db",
    "REDIS_URL": "redis://localhost:6379/0",
    "ALERT_ERROR_RATE_THRESHOLD": "0.05",
    "ALERT_P95_LATENCY_MS": "500",
    "ALERT_LOOKBACK_MIN": "10",
    "ALERT_CHANNELS": "slack,email",
    "SLACK_WEBHOOK_URL": "",
    "SMTP_HOST": "",
    "SMTP_PORT": "587",
    "SMTP_USER": "",
    "SMTP_PASS": "",
    "SMTP_FROM": "flowguard@demo.local",
    "SMTP_TO": "",
    "SERVICE_ALLOWLIST": "",
    "DEV_GENERATOR": "false",
    "CORS_ORIGINS": "*",
    "FLOWGUARD_ALERT_WINDOW_MIN": "10",
}


def _as_bool(value: str | bool | None) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _as_float(value: str | float, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _as_int(value: str | int, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _split_csv(value: str) -> List[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def load_config(env_path: Path | None = None) -> Dict[str, Any]:
    """Load environment variables and return a typed configuration mapping."""
    path = env_path or DEFAULT_ENV_PATH
    if path.exists():
        load_dotenv(path, override=False)

    cfg: Dict[str, Any] = {}
    for key, default in DEFAULTS.items():
        cfg[key] = os.getenv(key, default)

    cfg["ALERT_ERROR_RATE_THRESHOLD"] = _as_float(
        cfg["ALERT_ERROR_RATE_THRESHOLD"], default=0.05
    )
    cfg["ALERT_P95_LATENCY_MS"] = _as_int(cfg["ALERT_P95_LATENCY_MS"], default=500)
    cfg["ALERT_LOOKBACK_MIN"] = _as_int(cfg["ALERT_LOOKBACK_MIN"], default=10)
    cfg["FLOWGUARD_ALERT_WINDOW_MIN"] = _as_int(cfg["FLOWGUARD_ALERT_WINDOW_MIN"], default=10)
    cfg["SMTP_PORT"] = _as_int(cfg["SMTP_PORT"], default=587)
    cfg["ALERT_CHANNELS"] = _split_csv(cfg["ALERT_CHANNELS"])
    cfg["SERVICE_ALLOWLIST"] = _split_csv(cfg["SERVICE_ALLOWLIST"])
    cfg["DEV_GENERATOR"] = _as_bool(cfg["DEV_GENERATOR"])

    return cfg


def service_is_allowed(service: str, allowlist: Iterable[str]) -> bool:
    allow = {s.lower() for s in allowlist}
    return not allow or service.lower() in allow

