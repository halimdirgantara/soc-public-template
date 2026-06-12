#!/usr/bin/env bash
# ssh-triage.example.sh
#
# Query Loki for SSH authentication failures on a given host.
# Copy this file to ~/soc-tools/ssh-triage.sh on the Hermes node and make it executable.
#
# Usage:
#   ./ssh-triage.sh [host-regex] [range]
#
# Examples:
#   ./ssh-triage.sh "web-admin" "30m"
#   ./ssh-triage.sh ".*" "1h"
#
# Environment:
#   SOC_LOKI_URL  - Loki base URL (default: http://LOKI_SERVER_IP:3100)
#
# Public template: replace LOKI_SERVER_IP and the instansi label value
# before using in production.

set -euo pipefail

LOKI_URL="${SOC_LOKI_URL:-http://LOKI_SERVER_IP:3100}"
HOST="${1:-.*}"
RANGE="${2:-30m}"

QUERY="{instansi=\"example-org\", host=~\"${HOST}\"} \
|~ \"Failed password|Invalid user|authentication failure|Disconnected from authenticating user|PAM\""

curl -sG "${LOKI_URL}/loki/api/v1/query_range" \
  --data-urlencode "query=${QUERY}" \
  --data-urlencode "limit=100" \
  --data-urlencode "direction=backward" \
  --data-urlencode "start=$(date -u -d "${RANGE} ago" +%s)000000000" \
  --data-urlencode "end=$(date -u +%s)000000000" \
  | jq -r '
    .data.result[]? as $stream |
    $stream.values[]? |
    "\($stream.stream.host // "-") \($stream.stream.server_ip // "-") | \(.[1])"
  '
