"""SQLAlchemy ORM models for FlowGuard."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

LOG_LEVELS = ("DEBUG", "INFO", "WARN", "ERROR", "CRITICAL")


class Service(Base):
    __tablename__ = "services"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, nullable=False)
    created_ts = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    log_events = relationship("LogEvent", back_populates="service", cascade="all, delete-orphan")
    metric_points = relationship(
        "MetricPoint", back_populates="service", cascade="all, delete-orphan"
    )
    alerts = relationship("AlertEvent", back_populates="service", cascade="all, delete-orphan")

    def __repr__(self) -> str:  # pragma: no cover - introspection helper
        return f"<Service id={self.id} name={self.name}>"


class LogEvent(Base):
    __tablename__ = "log_events"

    id = Column(Integer, primary_key=True)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=False, index=True)
    ts = Column(DateTime(timezone=True), nullable=False, index=True)
    level = Column(Enum(*LOG_LEVELS, name="log_level_enum"), nullable=False, index=True)
    message = Column(String(2048), nullable=False)
    latency_ms = Column(Integer)
    status_code = Column(Integer)
    meta = Column(JSON, default=dict, nullable=False)
    created_ts = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    service = relationship("Service", back_populates="log_events")

    def __repr__(self) -> str:  # pragma: no cover - introspection helper
        return f"<LogEvent id={self.id} service={self.service_id} level={self.level}>"


class MetricPoint(Base):
    __tablename__ = "metric_points"
    __table_args__ = (
        UniqueConstraint("service_id", "ts", name="uq_metric_point_service_ts"),
    )

    id = Column(Integer, primary_key=True)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=False, index=True)
    ts = Column(DateTime(timezone=True), nullable=False, index=True)
    tps = Column(Numeric(10, 4), nullable=False)
    error_rate = Column(Numeric(10, 4), nullable=False)
    p95_latency_ms = Column(Integer, nullable=False)
    created_ts = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    service = relationship("Service", back_populates="metric_points")

    def __repr__(self) -> str:  # pragma: no cover - introspection helper
        return f"<MetricPoint id={self.id} service={self.service_id} ts={self.ts}>"


class AlertEvent(Base):
    __tablename__ = "alert_events"
    __table_args__ = (
        UniqueConstraint("dedupe_key", name="uq_alert_dedupe_key"),
    )

    id = Column(Integer, primary_key=True)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=False, index=True)
    ts = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    channel = Column(Enum("slack", "email", name="alert_channel_enum"), nullable=False)
    severity = Column(Enum("info", "warn", "critical", name="alert_severity_enum"), nullable=False)
    message = Column(String(1024), nullable=False)
    dedupe_key = Column(String(255), nullable=False)
    created_ts = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    service = relationship("Service", back_populates="alerts")

    def __repr__(self) -> str:  # pragma: no cover - introspection helper
        return f"<AlertEvent id={self.id} service={self.service_id} channel={self.channel}>"

