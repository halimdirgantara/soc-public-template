#!/usr/bin/env bash
set -euo pipefail

INVENTORY="${1:-inventory/hosts.example.csv}"

if [ ! -f "$INVENTORY" ]; then
  echo "[ERROR] Inventory not found: $INVENTORY"
  exit 1
fi

echo "[INFO] Reading inventory: $INVENTORY"

tail -n +2 "$INVENTORY" | while IFS=',' read -r host server_ip public_ip hostname exposure_type ssh_user ssh_port role enabled; do
  if [ "$enabled" != "true" ]; then
    echo "[SKIP] $host disabled"
    continue
  fi

  echo "[INFO] Would deploy Promtail to $host ($server_ip) as $ssh_user:$ssh_port"
  echo "[INFO] Public template dry-run only. Replace with your private deployment logic."

  # Important:
  # Use ssh -n or a dedicated file descriptor so SSH does not consume the loop STDIN.
  # Example:
  # ssh -n -p "$ssh_port" "$ssh_user@$server_ip" "hostname"
done