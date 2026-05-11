"""Signal endpoints + WebSocket."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.websocket import websocket_manager
from app.core.logging import get_logger
from app.db.session import get_db
from app.models.signal import Signal
from app.schemas.signal import SignalOut

router = APIRouter()
log = get_logger(__name__)


@router.get("", response_model=list[SignalOut], summary="List recent signals")
async def list_signals(
    db: AsyncSession = Depends(get_db),
    limit: int = Query(default=50, ge=1, le=500),
) -> list[Signal]:
    rows = await db.execute(select(Signal).order_by(Signal.created_at.desc()).limit(limit))
    return list(rows.scalars().all())


@router.websocket("/ws")
async def signals_ws(ws: WebSocket) -> None:
    """Subscribe to real-time signal broadcasts."""
    await websocket_manager.connect(ws)
    try:
        while True:
            # We don't accept input — just keep the connection alive.
            await ws.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        await websocket_manager.disconnect(ws)
