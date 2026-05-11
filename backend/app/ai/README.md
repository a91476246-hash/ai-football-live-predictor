# ai — Prediction Engine & Signal Classifier

## Files

| File | Purpose |
|---|---|
| `features.py` | Per-component feature extractors (form, pressure, 2H stats, odds). |
| `prediction_engine.py` | Async `PredictionEngine` implementing the weighted FinalScore formula. |
| `signal_classifier.py` | Buckets probabilities into Weak/Medium/Strong with rendered messages. |

## FinalScore formula

```
FinalScore = TeamForm * 0.25
           + LivePressure * 0.35
           + SecondHalfStats * 0.25
           + OddsMovement * 0.15
```

Every feature returns a value in `[0.0, 1.0]`, so the final score is itself a probability-shaped number in `[0.0, 1.0]`.

## Strength thresholds

Configurable via env:

| Bucket | Default |
|---|---|
| Weak | `0.60 ≤ p < 0.70` |
| Medium | `0.70 ≤ p < 0.80` |
| Strong | `p ≥ 0.80` |

## Future ML model

`PredictionEngine` is intentionally stateless and accepts an injected feature provider, so a future ML model (e.g. gradient-boosted trees in scikit-learn) can replace the weighted aggregation while reusing the same feature pipeline.
