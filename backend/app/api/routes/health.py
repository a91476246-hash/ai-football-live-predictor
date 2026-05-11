"""Health endpoint."""

from __future__ import annotations

from fastapi import APIRouter

from app import __version__

router = APIRouter()


@router.get("/health", summary="Service health-check")
async def health() -> dict[str, str]:
    return {"status": "ok", "version": __version__}
