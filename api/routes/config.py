"""Configuration endpoint for exposing runtime settings."""

from flask import Blueprint, jsonify

from api.utils.config import load_config

bp = Blueprint("config", __name__, url_prefix="/api")


@bp.get("/config")
def get_config() -> tuple[dict, int]:
    config = load_config()
    payload = {
        "db_url": config["DB_URL"],
        "redis_url": config["REDIS_URL"],
        "alert_error_rate_threshold": config["ALERT_ERROR_RATE_THRESHOLD"],
        "alert_p95_latency_ms": config["ALERT_P95_LATENCY_MS"],
        "alert_lookback_min": config["ALERT_LOOKBACK_MIN"],
        "alert_channels": config["ALERT_CHANNELS"],
        "services": config["SERVICE_ALLOWLIST"],
    }
    return jsonify(payload), 200
