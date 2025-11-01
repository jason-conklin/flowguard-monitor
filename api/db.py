"""Database helpers for FlowGuard."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Generator

from loguru import logger
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import scoped_session, sessionmaker

from api.models import Base

_engine: Engine | None = None
SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False))


def init_db(db_url: str) -> None:
    """Initialise the database engine and create tables if needed."""
    global _engine
    if _engine is not None:
        return

    logger.info("Initialising database engine", db_url=db_url)
    _engine = create_engine(db_url, future=True, pool_pre_ping=True)
    SessionLocal.configure(bind=_engine)
    Base.metadata.create_all(bind=_engine)


@contextmanager
def session_scope() -> Generator:
    """Provide a transactional scope around a series of operations."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:  # pragma: no cover - defensive
        session.rollback()
        raise
    finally:
        SessionLocal.remove()
