"""Alert-related endpoints."""

from __future__ import annotations

from flask import Blueprint, current_app, jsonify, request

from ..db import session_scope
from ..services.alerts import dispatch_test_alert

bp = Blueprint("alerts", __name__, url_prefix="/api")


@bp.post("/test-alert")
def test_alert() -> tuple[dict, int]:
    service = request.json.get("service") if request.is_json else None
    config = current_app.config

    with session_scope() as session:
        result = dispatch_test_alert(session, config, service_name=service)

    return jsonify(result), 202

