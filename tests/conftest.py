"""Pytest fixtures shared across the test suite."""

from __future__ import annotations

import os

# Force an in-memory database before app modules are imported.
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("TELEGRAM_ENABLED", "false")
os.environ.setdefault("LOG_LEVEL", "WARNING")
