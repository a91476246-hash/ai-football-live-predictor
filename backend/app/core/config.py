"""Application configuration via Pydantic settings."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Strongly-typed runtime configuration loaded from env / .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "AI Football Live Predictor"
    log_level: str = "INFO"
    debug: bool = False

    # Database
    database_url: str = "sqlite+aiosqlite:///./predictor.db"

    # Flashscore / Playwright
    flashscore_url: str = "https://www.flashscore.com/"
    headless: bool = True
    playwright_timeout_ms: int = 20_000

    # Live monitor
    monitor_interval_seconds: int = 30
    min_minute: int = 50

    # Signal thresholds (probability of goal in 2nd half)
    signal_threshold_weak: float = Field(default=0.60, ge=0.0, le=1.0)
    signal_threshold_medium: float = Field(default=0.70, ge=0.0, le=1.0)
    signal_threshold_strong: float = Field(default=0.80, ge=0.0, le=1.0)

    # Telegram
    telegram_bot_token: str | None = None
    telegram_chat_id: str | None = None
    telegram_enabled: bool = False


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
