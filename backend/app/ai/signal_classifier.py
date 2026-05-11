"""Signal classifier — buckets a probability into Weak / Medium / Strong."""

from __future__ import annotations

from dataclasses import dataclass

from app.ai.prediction_engine import PredictionResult
from app.core.config import get_settings
from app.models.signal import SignalStrength


@dataclass(slots=True)
class SignalDecision:
    """Output of :class:`SignalClassifier.classify`."""

    should_emit: bool
    strength: SignalStrength | None
    probability: float
    headline: str
    body: str

    def as_telegram_text(self) -> str:
        if not self.should_emit or self.strength is None:
            return ""
        icon = {
            SignalStrength.WEAK: "⚠️",
            SignalStrength.MEDIUM: "🚨",
            SignalStrength.STRONG: "🔥",
        }[self.strength]
        return f"{icon} {self.headline}\n\n{self.body}"


class SignalClassifier:
    """Classify prediction probability into a strength bucket and message."""

    def __init__(
        self,
        *,
        weak: float | None = None,
        medium: float | None = None,
        strong: float | None = None,
    ) -> None:
        settings = get_settings()
        self._weak = weak if weak is not None else settings.signal_threshold_weak
        self._medium = medium if medium is not None else settings.signal_threshold_medium
        self._strong = strong if strong is not None else settings.signal_threshold_strong

    def classify(self, result: PredictionResult) -> SignalDecision:
        probability = result.probability
        strength = self._bucket(probability)
        if strength is None:
            return SignalDecision(
                should_emit=False,
                strength=None,
                probability=probability,
                headline="",
                body="",
            )
        match = result.match
        headline = f"{strength.value.upper()} SIGNAL — {match.home_team} vs {match.away_team}"
        body = (
            f"⏱ Minute: {match.minute}'\n"
            f"📊 Goal Probability (2H): {probability * 100:.1f}%\n"
            f"🎯 Prediction: GOAL IN 2ND HALF\n"
            f"⚽ Expected Goals: {result.expected_goals_min:.1f}-{result.expected_goals_max:.1f}\n"
            f"🔬 Breakdown: form={result.breakdown.team_form:.2f}, "
            f"pressure={result.breakdown.live_pressure:.2f}, "
            f"2H={result.breakdown.second_half_stats:.2f}, "
            f"odds={result.breakdown.odds_movement:.2f}"
        )
        return SignalDecision(
            should_emit=True,
            strength=strength,
            probability=probability,
            headline=headline,
            body=body,
        )

    def _bucket(self, probability: float) -> SignalStrength | None:
        if probability >= self._strong:
            return SignalStrength.STRONG
        if probability >= self._medium:
            return SignalStrength.MEDIUM
        if probability >= self._weak:
            return SignalStrength.WEAK
        return None
