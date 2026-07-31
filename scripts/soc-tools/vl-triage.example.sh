#!/usr/bin/env bash
# vl-triage.example.sh
#
# Query VictoriaLogs for Laravel application errors on a given host.
# Copy this file to ~/soc-tools/vl-triage.sh on the Hermes node and make it executable.
#
# Usage:
#   ./vl-triage.sh <host-regex> [app-regex] [range]
#
# Examples:
#   ./vl-triage.sh "web-admin" ".*" "30m"
#   ./vl-triage.sh "web-.*" "web-opd-filament" "1h"
#
# Environment:
#   SOC_VL_URL  - VictoriaLogs query URL (default: http://VL_SERVER_IP:9428/select/logsql/query)
#
# Public template: replace VL_SERVER_IP and the instansi label value
# before using in production.

set -euo pipefail

VL_URL="${SOC_VL_URL:-http://VL_SERVER_IP:9428/select/logsql/query}"
HOST="${1:-}"
APP="${2:-.*}"
RANGE="${3:-15m}"

if [ -z "$HOST" ]; then
  echo "Usage: $0 <host-regex> [app-regex] [range]"
  exit 1
fi

# LogsQL — time filter, stream filter, regex on message
QUERY="_time:${RANGE} _stream:{instansi=\"example-org\", job=\"laravel\", host=~\"${HOST}\"} ~\"(?i)(error|exception|critical|warning|failed|production.ERROR)\" | limit 50"

curl -sG "${VL_URL}" \
  --data-urlencode "query=${QUERY}" \
  | jq -r '
    "\(.host // "-") \(.server_ip // "-") \(.app // "-") | \(._time // "-")\n\(._msg // "")\n---"
  '
