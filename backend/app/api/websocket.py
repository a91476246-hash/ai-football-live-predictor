"""WebSocket broadcaster for live signals."""

from __future__ import annotations

import asyncio

from fastapi import WebSocket

from app.core.logging import get_logger
from app.schemas.signal import SignalOut

log = get_logger(__name__)


class WebSocketManager:
    """Tracks connected WebSocket clients and broadcasts payloads to all of them."""

    def __init__(self) -> None:
        self._connections: set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        async with self._lock:
            self._connections.add(ws)
        log.info("ws.connect", clients=len(self._connections))

    async def disconnect(self, ws: WebSocket) -> None:
        async with self._lock:
            self._connections.discard(ws)
        log.info("ws.disconnect", clients=len(self._connections))

    async def broadcast(self, payload: SignalOut) -> None:
        async with self._lock:
            targets = list(self._connections)
        if not targets:
            return
        data = payload.model_dump(mode="json")
        for ws in targets:
            try:
                await ws.send_json(data)
            except Exception:
                log.warning("ws.send_failed")
                await self.disconnect(ws)


websocket_manager = WebSocketManager()
