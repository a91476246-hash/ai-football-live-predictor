"""Domain-specific exceptions."""

from __future__ import annotations


class PredictorError(Exception):
    """Base error for the predictor backend."""


class ParserError(PredictorError):
    """Raised when a parser fails to extract data."""


class ProviderError(PredictorError):
    """Raised when an external data provider is unreachable or invalid."""


class TelegramError(PredictorError):
    """Raised when the Telegram client fails."""


class PredictionError(PredictorError):
    """Raised when the prediction engine cannot score a match."""
