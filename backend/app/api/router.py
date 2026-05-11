"""Top-level API router."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.routes import health, matches, predictions, signals

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(matches.router, prefix="/matches", tags=["matches"])
api_router.include_router(predictions.router, prefix="/predictions", tags=["predictions"])
api_router.include_router(signals.router, prefix="/signals", tags=["signals"])
