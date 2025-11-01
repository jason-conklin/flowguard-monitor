"""Flask application factory for FlowGuard API."""

from flask import Flask, jsonify
from flask_cors import CORS
from loguru import logger

from .db import init_db, SessionLocal
from .utils.config import load_config
from .services.celery_app import init_celery
from .routes.health import bp as health_bp
from .routes.ingest import bp as ingest_bp
from .routes.query import bp as query_bp
from .routes.alerts import bp as alerts_bp
from .routes.config import bp as config_bp


def create_app(config_override: dict | None = None) -> Flask:
    """Application factory used by both the Flask dev server and gunicorn."""
    app = Flask(__name__)

    config = load_config()
    if config_override:
        config.update(config_override)
    app.config.update(config)

    CORS(app, resources={r"/api/*": {"origins": app.config.get("CORS_ORIGINS", "*")}})
    init_db(app.config["DB_URL"])
    init_celery(app)

    for blueprint in (health_bp, ingest_bp, query_bp, alerts_bp, config_bp):
        app.register_blueprint(blueprint)

    @app.route("/", methods=["GET"])
    def root() -> tuple[dict[str, str], int]:
        return jsonify({"service": "flowguard", "status": "ok"}), 200

    @app.teardown_appcontext
    def shutdown_session(_exc: Exception | None = None) -> None:
        SessionLocal.remove()

    @app.before_request
    def _log_request() -> None:
        logger.bind(component="api").debug("Handling request")

    return app


if __name__ == "__main__":
    create_app().run(host="0.0.0.0", port=8000, debug=False)

