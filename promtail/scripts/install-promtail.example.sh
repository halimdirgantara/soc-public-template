#!/usr/bin/env bash
set -euo pipefail

LOKI_PUSH_URL="${LOKI_PUSH_URL:-http://10.0.0.10:3100/loki/api/v1/push}"
ORG_LABEL="${ORG_LABEL:-example-org}"
SERVER_IP="${SERVER_IP:-$(hostname -I | awk "{print \$1}")}"
HOSTNAME_VALUE="${HOSTNAME_VALUE:-$(hostname)}"

echo "[INFO] Installing Promtail template"
echo "[INFO] LOKI_PUSH_URL=${LOKI_PUSH_URL}"
echo "[INFO] ORG_LABEL=${ORG_LABEL}"
echo "[INFO] SERVER_IP=${SERVER_IP}"
echo "[INFO] HOSTNAME=${HOSTNAME_VALUE}"

mkdir -p /etc/promtail /var/lib/promtail
# Place promtail binary manually or install from your package source.
# This public template intentionally does not download binaries from a specific production source.

if ! command -v promtail >/dev/null 2>&1 && [ ! -x /usr/local/bin/promtail ]; then
  echo "[WARN] promtail binary not found. Install promtail first, then re-run."
fi

echo "[INFO] Render /etc/promtail/config.yml from template in your private repo or CI/CD."
echo "[DONE] Promtail installation placeholder completed."