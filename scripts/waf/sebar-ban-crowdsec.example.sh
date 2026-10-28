#!/bin/bash
# Contoh sebar/cabut keputusan CrowdSec.
#
# Mode lokal (dijalankan di host):
#   sudo ./sebar-ban-crowdsec.example.sh add 203.0.113.10 [durasi]
#   sudo ./sebar-ban-crowdsec.example.sh del 203.0.113.10
#
# Mode armada (dari jump host dengan SSH key):
#   ./sebar-ban-crowdsec.example.sh fleet 203.0.113.10 /path/hosts.txt
#
# Catatan: ban ini hanya menahan koneksi LANGSUNG ke origin. Untuk trafik yang
# melewati CDN, gunakan WAF berbasis IP asli (lihat nginx/ dan scripts/waf/).
set -u

MODE=${1:-}
IP=${2:-}
ARG=${3:-24h}

[ -n "$IP" ] || { echo "Pakai: $0 {add|del|fleet} <IP> [durasi|file-host]"; exit 1; }

case "$MODE" in
  add)
    cscli decisions add --ip "$IP" --duration "$ARG" --type ban --reason "manual SOC" 2>&1 | tail -1
    cscli decisions list --ip "$IP" 2>/dev/null | grep -c "ban" | sed 's/^/decision aktif: /'
    ;;
  del)
    cscli decisions delete --ip "$IP" 2>&1 | tail -1
    ;;
  fleet)
    LIST=$ARG
    [ -f "$LIST" ] || { echo "Daftar host tidak ada: $LIST"; exit 1; }
    while read -r h; do
      [ -z "$h" ] && continue
      out=$(ssh -o BatchMode=yes -o ConnectTimeout=8 "root@$h" \
        "cscli decisions add --ip '$IP' --duration 24h --type ban --reason 'manual SOC' >/dev/null 2>&1 && cscli decisions list --ip '$IP' | grep -c ban" 2>/dev/null)
      printf '%-24s %s\n' "$h" "${out:-GAGAL}"
    done < "$LIST"
    ;;
  *)
    echo "Mode tidak dikenal: $MODE"; exit 1
    ;;
esac
