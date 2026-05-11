"""End-to-end tests for the FastAPI app."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.db.init_db import init_models
from app.main import app


@pytest.fixture(autouse=True)
async def _setup_db() -> None:
    await init_models()


async def test_health() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


async def test_lists_are_initially_empty() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        for path in ("/matches", "/predictions", "/signals"):
            resp = await client.get(path)
            assert resp.status_code == 200
            assert resp.json() == []
