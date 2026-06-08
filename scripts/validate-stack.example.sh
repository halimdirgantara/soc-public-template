#!/usr/bin/env bash
set -euo pipefail

LOKI_URL="${LOKI_URL:-http://10.0.0.10:3100}"

echo "[INFO] Validating Loki"
curl -fsS "$LOKI_URL/ready" || echo "[WARN] Loki /ready failed"
curl -fsS "$LOKI_URL/loki/api/v1/labels" || echo "[WARN] Loki labels failed"

echo "[INFO] Validating local services if present"
for svc in grafana-server promtail crowdsec crowdsec-firewall-bouncer; do
  if systemctl list-unit-files | grep -q "^${svc}"; then
    systemctl status "$svc" --no-pager || true
  else
    echo "[SKIP] $svc not installed"
  fi
done

echo "[DONE] Validation completed"