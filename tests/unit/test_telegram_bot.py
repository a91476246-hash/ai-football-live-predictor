"""Tests for the Telegram client."""

from __future__ import annotations

import httpx

from app.telegram.bot import TelegramClient

_ORIG_ASYNC_CLIENT = httpx.AsyncClient


def _patch_async_client(monkeypatch, handler):  # type: ignore[no-untyped-def]
    transport = httpx.MockTransport(handler)

    def _factory(*_args, **_kwargs):  # type: ignore[no-untyped-def]
        return _ORIG_ASYNC_CLIENT(transport=transport)

    monkeypatch.setattr("app.telegram.bot.httpx.AsyncClient", _factory)


def _ok_handler(_request: httpx.Request) -> httpx.Response:
    return httpx.Response(200, json={"ok": True, "result": {}})


def _4xx_handler(_request: httpx.Request) -> httpx.Response:
    return httpx.Response(400, json={"ok": False, "description": "bad request"})


async def test_send_message_ok(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    _patch_async_client(monkeypatch, _ok_handler)
    client = TelegramClient(token="x", chat_id="123")
    assert await client.send_message("hello") is True


async def test_send_message_4xx_returns_false(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    _patch_async_client(monkeypatch, _4xx_handler)
    client = TelegramClient(token="x", chat_id="123")
    assert await client.send_message("hello") is False


async def test_empty_text_returns_false() -> None:
    client = TelegramClient(token="x", chat_id="123")
    assert await client.send_message("") is False
