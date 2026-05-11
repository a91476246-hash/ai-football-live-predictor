# frontend

Reserved for the Phase 4 React + Tailwind dashboard.

## Planned features

* Live matches grid (auto-updates via `/signals/ws`).
* Match detail view with stats and prediction breakdown.
* Filters by league, minute, probability, odds.
* Historical signal log with ROI tracker.
* Settings (signal thresholds, Telegram on/off).

The backend is fully prepared to support this UI — REST endpoints under `/matches`, `/predictions`, `/signals` plus the WebSocket at `/signals/ws`. See [`../backend/app/api/README.md`](../backend/app/api/README.md).
