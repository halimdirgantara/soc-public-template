#!/usr/bin/env bash
# loki-triage.example.sh
#
# Query Loki for Laravel application errors on a given host.
# Copy this file to ~/soc-tools/loki-triage.sh on the Hermes node and make it executable.
#
# Usage:
#   ./loki-triage.sh <host-regex> [app-regex] [range]
#
# Examples:
#   ./loki-triage.sh "web-admin" ".*" "30m"
#   ./loki-triage.sh "web-.*" "web-opd-filament" "1h"
#
# Environment:
#   SOC_LOKI_URL  - Loki base URL (default: http://LOKI_SERVER_IP:3100)
#
# Public template: replace LOKI_SERVER_IP and the instansi label value
# before using in production.

set -euo pipefail

LOKI_URL="${SOC_LOKI_URL:-http://LOKI_SERVER_IP:3100}"
HOST="${1:-}"
APP="${2:-.*}"
RANGE="${3:-15m}"

if [ -z "$HOST" ]; then
  echo "Usage: $0 <host-regex> [app-regex] [range]"
  exit 1
fi

QUERY="{instansi=\"example-org\", job=\"laravel\", host=~\"${HOST}\", app=~\"${APP}\"} \
|~ \"(?i)(error|exception|critical|warning|failed|production.ERROR)\""

curl -sG "${LOKI_URL}/loki/api/v1/query_range" \
  --data-urlencode "query=${QUERY}" \
  --data-urlencode "limit=50" \
  --data-urlencode "direction=backward" \
  --data-urlencode "start=$(date -u -d "${RANGE} ago" +%s)000000000" \
  --data-urlencode "end=$(date -u +%s)000000000" \
  | jq -r '
    .data.result[]? as $stream |
    $stream.values[]? |
    "\(.[0]) \($stream.stream.host // "-") \($stream.stream.server_ip // "-") \($stream.stream.app // "-")\n\(.[1])\n---"
  '
