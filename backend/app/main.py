"""FastAPI entry point."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.api.websocket import websocket_manager
from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.db.init_db import dispose_engine, init_models
from app.schemas.signal import SignalOut

log = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan: init DB on startup, dispose on shutdown."""
    configure_logging()
    settings = get_settings()
    log.info("app.startup", name=settings.app_name)
    await init_models()
    try:
        yield
    finally:
        log.info("app.shutdown")
        await dispose_engine()


def create_app() -> FastAPI:
    """FastAPI application factory."""
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        debug=settings.debug,
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api_router)

    async def _broadcast(payload: SignalOut) -> None:
        await websocket_manager.broadcast(payload)

    # Expose the broadcaster on app.state so other components (like a
    # background monitor) can wire themselves in if started in-process.
    app.state.broadcast_signal = _broadcast
    return app


app = create_app()
