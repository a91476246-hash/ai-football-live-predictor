"""Database initialization (create_all for SQLite/local dev)."""

from __future__ import annotations

from app.core.logging import get_logger
from app.db.base import Base
from app.db.session import engine
from app.models import (  # noqa: F401 - register models
    match,
    prediction,
    signal,
    team_stats,
)

log = get_logger(__name__)


async def init_models() -> None:
    """Create database tables if they don't exist."""
    log.info("db.init.start")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    log.info("db.init.done")


async def dispose_engine() -> None:
    """Close all connections (called on shutdown)."""
    await engine.dispose()
