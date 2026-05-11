# api — REST + WebSocket

FastAPI router exposing the predictor's REST surface and the WebSocket stream.

## Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Health-check (returns version). |
| GET | `/matches` | Recently observed matches. |
| GET | `/predictions` | Predictions emitted by the engine. |
| GET | `/signals` | Recent user-facing signals. |
| WS  | `/signals/ws` | Live signal broadcast stream. |

OpenAPI docs available at `/docs` (Swagger UI) and `/redoc`.

## WebSocket payload

Server emits a JSON `SignalOut` on every new signal. Clients can ignore inbound messages — the connection is server-push only.

```jsonc
{
  "id": 42,
  "match_id": 7,
  "strength": "strong",
  "probability": 0.83,
  "headline": "STRONG SIGNAL — Chelsea vs Arsenal",
  "body": "...",
  "delivered": true,
  "created_at": "2026-05-11T12:34:56Z"
}
```
