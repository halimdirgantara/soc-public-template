#!/usr/bin/env bash
# ssh-triage.example.sh
#
# Query VictoriaLogs for SSH authentication failures on a given host.
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
#   SOC_VL_URL  - VictoriaLogs query URL (default: http://VL_SERVER_IP:9428/select/logsql/query)
#
# Public template: replace VL_SERVER_IP and the instansi label value
# before using in production.

set -euo pipefail

VL_URL="${SOC_VL_URL:-http://VL_SERVER_IP:9428/select/logsql/query}"
HOST="${1:-.*}"
RANGE="${2:-30m}"

# LogsQL — auth failures grouped per source IP
QUERY="_time:${RANGE} _stream:{instansi=\"example-org\", job=\"auth\", host=~\"${HOST}\"} ~\"(?i)(Failed password|Invalid user|authentication failure|Disconnected from authenticating user|PAM)\" | limit 100"

curl -sG "${VL_URL}" \
  --data-urlencode "query=${QUERY}" \
  | jq -r '"\(.host // "-") \(.server_ip // "-") | \(._msg // "")"'
