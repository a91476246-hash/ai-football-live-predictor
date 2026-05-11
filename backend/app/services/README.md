# services — Orchestration

| File | Purpose |
|---|---|
| `live_monitor.py` | Async polling loop: fetch → filter → predict → dispatch. |
| `signal_dispatcher.py` | Persist signals to DB and fan out to Telegram + WebSocket. |

## Filter

A match is a candidate only if:

* status is `2H`
* score is `0:0`
* minute is `>= MIN_MINUTE` (default 50)

## CLI

`pip install -e backend/` exposes the `afp-monitor` console script.

```bash
afp-monitor
```

It builds the default wiring (Flashscore + Telegram) and runs the loop until SIGTERM/SIGINT.
