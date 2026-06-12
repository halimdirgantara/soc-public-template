#!/usr/bin/env bash
# Public template only. Sanitized example.
# Copy to your private repo and adapt for real inventory.
# See docs/05-fail2ban-hermes-prep.md for the full workflow.

set -euo pipefail

HOST="${1:?Usage: $0 user@host}"
KEY="${SSH_KEY:-$HOME/.ssh/id_rsa}"

ssh -i "$KEY" -o BatchMode=yes -o ConnectTimeout=8 "$HOST" '
echo HOSTNAME=$(hostname)
echo USER=$(whoami)
echo SUDO=$(sudo -n true && echo OK || echo BAD)
echo FAIL2BAN=$(systemctl is-active fail2ban 2>/dev/null || echo inactive)
echo PROMTAIL=$(systemctl is-active promtail 2>/dev/null || echo missing)
echo UFW=$(sudo ufw status | head -n1)
echo
sudo fail2ban-client status sshd 2>/dev/null || true
'
