# Telegram Alert Setup

Do not commit Telegram credentials.

## Required values

```env
TELEGRAM_BOT_TOKEN=change-me
TELEGRAM_CHAT_ID=change-me
```

## Alert Principles

- Preserve useful labels: `host`, `server_ip`, `src_ip`.
- Set No Data to `Normal` or `OK`.
- Exclude internal scanners.
- Start with conservative thresholds.
- Tune after observing baseline traffic.