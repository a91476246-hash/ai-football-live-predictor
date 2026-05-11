# telegram — Bot integration

Minimal async client for Telegram Bot API. No SDK dependency — just `httpx`.

## Configuration

| Env | Description |
|---|---|
| `TELEGRAM_ENABLED` | Master switch (`true` / `false`). |
| `TELEGRAM_BOT_TOKEN` | Token from @BotFather. |
| `TELEGRAM_CHAT_ID` | Target chat or channel ID. |

## Setup steps

1. Talk to [@BotFather](https://t.me/BotFather), create a bot, copy the token.
2. Add the bot to your target chat or channel.
3. Find the chat ID via [@userinfobot](https://t.me/userinfobot) or by calling `GET /getUpdates`.
4. Set the three env vars and restart.

`SignalDispatcher` automatically uses the Telegram sender if `build_telegram_sender()` returns a non-`None` coroutine.
