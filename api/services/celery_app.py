"""Celery application factory for FlowGuard."""

from __future__ import annotations

from celery import Celery
from flask import Flask
from loguru import logger

from ..utils.config import load_config

celery = Celery("flowguard")


def init_celery(app: Flask | None = None) -> Celery:
    """Configure and return the Celery application."""
    config = load_config()
    celery.conf.update(
        broker_url=config["REDIS_URL"],
        result_backend=config["REDIS_URL"],
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        timezone="UTC",
        enable_utc=True,
        task_track_started=True,
        include=["services.pipeline"],
    )

    if app is not None:
        celery.conf.update(app.config)

    logger.info("Celery configured", broker=celery.conf.broker_url)
    return celery


# Ensure celery is initialised on import for worker processes.
init_celery()
