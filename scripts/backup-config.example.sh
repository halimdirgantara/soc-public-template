#!/usr/bin/env bash
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-./backups}"
STAMP="$(date +%Y%m%d_%H%M%S)"
OUT="$BACKUP_DIR/soc-config-$STAMP.tar.gz"

mkdir -p "$BACKUP_DIR"

PATHS=(
  /etc/loki
  /etc/promtail
  /etc/grafana
  /etc/crowdsec
  /etc/nginx
  /etc/cloudflared
)

EXISTING=()
for p in "${PATHS[@]}"; do
  if [ -e "$p" ]; then
    EXISTING+=("$p")
  fi
done

if [ "${#EXISTING[@]}" -eq 0 ]; then
  echo "[WARN] No config paths found to backup"
  exit 0
fi

sudo tar --exclude='*.key' --exclude='*.pem' --exclude='credentials.json' -czf "$OUT" "${EXISTING[@]}"
echo "[DONE] Backup created: $OUT"
