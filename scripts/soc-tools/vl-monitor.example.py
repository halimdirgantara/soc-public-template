#!/usr/bin/env python3
"""
vl-monitor.example.py — VictoriaLogs watchdog bot (production pattern).

Polls VictoriaLogs LogsQL queries every N minutes and sends Telegram
notifications when a threshold is exceeded. This is the recommended alert
path for low-resource SOC deployments: no Grafana alert rules needed.

Copy to ~/.hermes/scripts/vl-monitor.py on the Hermes node, set the
environment variables, and schedule via cron:

    */5 * * * * cd ~ && /usr/bin/python3 ~/.hermes/scripts/vl-monitor.py >> ~/.hermes/logs/vl-monitor.log 2>&1

Environment:
  SOC_VL_URL      VictoriaLogs query endpoint (default http://VL_SERVER_IP:9428/select/logsql/query)
  TELEGRAM_BOT_TOKEN  Telegram bot token (never commit!)
  TELEGRAM_CHAT_ID    Telegram chat/channel ID to notify
"""

import json
import os
import sys
import time
import urllib.parse
import urllib.request

VL_URL = os.environ.get("SOC_VL_URL", "http://VL_SERVER_IP:9428/select/logsql/query")
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
INSTANSI = os.environ.get("SOC_INSTANSI", "example-org")

# (name, LogsQL query, min_count) — adjust thresholds per deployment
QUERIES = [
    (
        "SSH brute-force",
        f'_time:5m _stream:{{instansi="{INSTANSI}", job="auth"}} '
        '~"(?i)(Failed password|Invalid user|authentication failure)" | limit 100',
        5,
    ),
    (
        "Laravel error",
        f'_time:5m _stream:{{instansi="{INSTANSI}", job="laravel"}} '
        '"production.ERROR" | limit 20',
        1,
    ),
    (
        "UFW block",
        f'_time:10m _stream:{{instansi="{INSTANSI}"}} "UFW BLOCK" | stats by (host) count() hits | filter hits >= 10',
        1,
    ),
]


def query_logs(query: str) -> list:
    params = urllib.parse.urlencode({"query": query})
    url = f"{VL_URL}?{params}"
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        raw = resp.read().decode()
    if not raw.strip():
        return []
    return [json.loads(line) for line in raw.splitlines() if line.strip()]


def send_telegram(text: str) -> None:
    if not BOT_TOKEN or not CHAT_ID:
        print(f"[SKIP] TELEGRAM_* not set: {text}")
        return
    data = urllib.parse.urlencode(
        {"chat_id": CHAT_ID, "text": text, "disable_web_page_preview": "true"}
    ).encode()
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    req = urllib.request.Request(url, data=data)
    with urllib.request.urlopen(req, timeout=15) as resp:
        resp.read()


def main() -> None:
    fired = []
    for name, query, threshold in QUERIES:
        try:
            rows = query_logs(query)
        except Exception as exc:  # noqa: BLE001
            print(f"[ERROR] {name}: {exc}")
            continue
        count = len(rows)
        if count >= threshold:
            hosts = sorted({r.get("host", "-") for r in rows})
            fired.append(
                f"⚠️ {name} — {count}x dlm rentang, host: {', '.join(hosts)}"
            )
        print(f"[{name}] count={count} threshold={threshold}")

    if fired:
        send_telegram("\n".join(fired))


if __name__ == "__main__":
    main()
