# AI Football Live Predictor

Real-time monitoring of football live matches with a focus on detecting **2nd-half goal opportunities** in scoreless games. Combines a live web parser (Flashscore via Playwright), historical team analytics, a weighted prediction engine, and a Telegram alert dispatcher.

> ⚠️ **Legal notice**: Scraping Flashscore violates their Terms of Service. The parser is included as a reference implementation; for production deployments swap it for an official data provider (api-football, Sportradar, BetsAPI). The architecture is built so the `LiveDataProvider` interface can be backed by any source.

---

## Highlights

- **Async-first** Python 3.12 backend (FastAPI + asyncio + SQLAlchemy 2.0 async).
- **Pluggable data providers** — `FlashscoreProvider` ships out of the box; swap for an API client without touching the rest of the stack.
- **Weighted prediction engine** using the formula from the spec:
  `FinalScore = TeamForm * 0.25 + LivePressure * 0.35 + SecondHalfStats * 0.25 + OddsMovement * 0.15`
- **Signal classifier** — Weak (60–69%), Medium (70–79%), Strong (80%+).
- **Telegram alerts** with structured, emoji-rich messages.
- **WebSocket stream** so a frontend can subscribe to live matches and signals.
- **Docker-ready** with multi-stage build and `docker-compose`.
- **Clean architecture**: parsers → services → engine → dispatcher, each module independently testable.
- **Retry, structured logging, typed everywhere**, ruff + mypy + pytest in CI.

---

## Architecture

```
                ┌────────────────────────┐
                │  Flashscore (or API)   │
                └───────────┬────────────┘
                            │ Playwright / HTTP
                ┌───────────▼────────────┐
                │   LiveDataProvider     │  parsers/
                └───────────┬────────────┘
                            │
                ┌───────────▼────────────┐
                │      LiveMonitor       │  services/live_monitor.py
                │  filter: HT2 & 0:0 &   │
                │       minute > 50      │
                └───────────┬────────────┘
                            │ candidate matches
                ┌───────────▼────────────┐
                │  TeamHistoryProvider   │  parsers/team_history.py
                │  last 5-10 matches     │
                └───────────┬────────────┘
                            │ features
                ┌───────────▼────────────┐
                │   PredictionEngine     │  ai/prediction_engine.py
                │  weighted FinalScore   │
                └───────────┬────────────┘
                            │ probability
                ┌───────────▼────────────┐
                │   SignalClassifier     │  ai/signal_classifier.py
                │   weak / medium / strong│
                └───────┬──────────┬─────┘
                        │          │
              ┌─────────▼──┐  ┌────▼─────────┐
              │ Telegram   │  │ WebSocket    │
              │ Dispatcher │  │ + REST API   │
              └────────────┘  └──────────────┘
```

---

## Quick start

```bash
# 1. clone
git clone https://github.com/<owner>/ai-football-live-predictor.git
cd ai-football-live-predictor

# 2. configure
cp backend/.env.example backend/.env
# edit TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID

# 3. run with docker (recommended)
docker compose -f docker/docker-compose.yml up --build

# OR run locally
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
playwright install chromium
uvicorn app.main:app --reload
```

The API will be at <http://localhost:8000>, OpenAPI docs at <http://localhost:8000/docs>, and the live websocket at `ws://localhost:8000/ws/signals`.

---

## Configuration

All settings are loaded via Pydantic settings from environment variables (or a `.env` file). See `backend/.env.example` for the full list.

| Key | Description | Default |
|---|---|---|
| `DATABASE_URL` | SQLAlchemy async URL | `sqlite+aiosqlite:///./predictor.db` |
| `TELEGRAM_BOT_TOKEN` | Bot token from @BotFather | — |
| `TELEGRAM_CHAT_ID` | Target chat ID | — |
| `FLASHSCORE_URL` | Live page URL | `https://www.flashscore.com/` |
| `MONITOR_INTERVAL_SECONDS` | Poll interval for live matches | `30` |
| `MIN_MINUTE` | Minimum match minute to consider | `50` |
| `SIGNAL_THRESHOLD_WEAK` | Lower bound for weak signal | `0.60` |
| `SIGNAL_THRESHOLD_MEDIUM` | Lower bound for medium signal | `0.70` |
| `SIGNAL_THRESHOLD_STRONG` | Lower bound for strong signal | `0.80` |
| `HEADLESS` | Run Playwright headless | `true` |
| `LOG_LEVEL` | structlog level | `INFO` |

---

## Modules

Each module has its own README:

- [`backend/app/api/README.md`](backend/app/api/README.md) — REST + WebSocket endpoints
- [`backend/app/parsers/README.md`](backend/app/parsers/README.md) — Flashscore, match, team history parsers
- [`backend/app/ai/README.md`](backend/app/ai/README.md) — prediction engine and signal classifier
- [`backend/app/services/README.md`](backend/app/services/README.md) — live monitor and signal dispatcher
- [`backend/app/telegram/README.md`](backend/app/telegram/README.md) — Telegram bot client
- [`backend/app/db/README.md`](backend/app/db/README.md) — database layer

---

## Development

```bash
cd backend
pip install -e ".[dev]"

# Lint
ruff check .
ruff format --check .

# Type check
mypy app

# Tests
pytest -v
```

CI runs lint, type-check, and the full test suite on every PR.

---

## Roadmap

- **Phase 1 (MVP)** — done: parser, monitor, prediction engine, Telegram alerts, REST/WebSocket API.
- **Phase 2** — richer team history features, league-aware weighting, historical backtesting harness.
- **Phase 3** — ML model (gradient boosted trees → optionally fine-tuned NN) trained on collected match-state snapshots, with auto-learning loop.
- **Phase 4** — React/Tailwind dashboard, multi-thread parser cluster, hosted deployment with monitoring.

---

## License

MIT — see [LICENSE](LICENSE).
