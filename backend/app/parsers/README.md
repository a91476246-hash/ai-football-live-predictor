# parsers — Data Providers

| File | Purpose |
|---|---|
| `base.py` | `LiveDataProvider` and `TeamHistoryProvider` abstract base classes. |
| `flashscore.py` | Playwright-based live-data provider. |
| `match_parser.py` | Pure HTML → `LiveMatch` parser (unit-testable). |
| `team_history.py` | `TeamHistory` aggregate + in-memory / Flashscore-backed providers. |

## Swapping the data source

Implement your own `LiveDataProvider` and pass it to `LiveMonitor`:

```python
class ApiFootballProvider(LiveDataProvider):
    async def start(self) -> None: ...
    async def stop(self) -> None: ...
    async def fetch_live_matches(self) -> list[LiveMatch]: ...
```

The rest of the pipeline is provider-agnostic.

## Testing parsers offline

Use the static HTML fixture in `tests/fixtures/match_card.html` with
`parse_match_card(...)` directly — no Playwright required.
