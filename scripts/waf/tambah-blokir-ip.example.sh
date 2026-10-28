#!/bin/bash
# Contoh tambah/hapus/lihat IP pada daftar blokir nginx & Caddy.
#
# Pakai:
#   sudo ./tambah-blokir-ip.example.sh add 203.0.113.10
#   sudo ./tambah-blokir-ip.example.sh del 203.0.113.10
#   sudo ./tambah-blokir-ip.example.sh list
set -u

AKSI=${1:-list}
IP=${2:-}
NGINX_MAP=${NGINX_MAP:-/www/server/nginx/conf/soc-waf-map.conf}
CADDY_SITES=${CADDY_SITES:-/etc/caddy/sites}

valid_ip() { echo "$1" | grep -qE '^([0-9]{1,3}\.){3}[0-9]{1,3}$|^[0-9a-fA-F:]+$'; }

reload_nginx() {
  systemctl reload nginx 2>/dev/null || /etc/init.d/nginx reload >/dev/null 2>&1 || nginx -s reload
  sleep 3
}

if [ "$AKSI" != "list" ]; then
  [ -n "$IP" ] && valid_ip "$IP" || { echo "IP tidak valid / kosong"; exit 1; }
fi

if [ -f "$NGINX_MAP" ]; then
  cp -p "$NGINX_MAP" "/root/soc-waf-map-$(date +%Y%m%d-%H%M%S).conf"
  case "$AKSI" in
    add)
      grep -qE "^\s*${IP//./\\.}\s+1;" "$NGINX_MAP" || sed -i "/map \$remote_addr \$soc_block_ip {/a\\    $IP 1;" "$NGINX_MAP"
      nginx -t >/dev/null 2>&1 && reload_nginx && echo "nginx: $IP ditambahkan"
      ;;
    del)
      sed -i "/^\s*${IP//./\\.}\s\+1;/d" "$NGINX_MAP"
      nginx -t >/dev/null 2>&1 && reload_nginx && echo "nginx: $IP dihapus"
      ;;
    list)
      echo "== nginx =="; sed -n '/map \$remote_addr \$soc_block_ip/,/}/p' "$NGINX_MAP" | grep -E "\s1;"
      ;;
  esac
fi

if [ -d "$CADDY_SITES" ] && command -v caddy >/dev/null 2>&1; then
  case "$AKSI" in
    add)
      python3 - "$CADDY_SITES" "$IP" <<'PY'
import sys, glob, re
sites, ip = sys.argv[1], sys.argv[2]
n = 0
for f in glob.glob(sites + "/*.caddy"):
    s = open(f, encoding="utf-8", errors="surrogateescape").read()
    m = re.search(r"@soc_block_ip client_ip ([^\n]+)", s)
    if not m or ip in m.group(1):
        continue
    s = s.replace(m.group(0), "@soc_block_ip client_ip " + m.group(1).strip() + " " + ip)
    open(f, "w", encoding="utf-8", errors="surrogateescape").write(s); n += 1
print("caddy: situs diperbarui", n)
PY
      caddy validate --config /etc/caddy/Caddyfile >/dev/null 2>&1 && systemctl reload caddy && sleep 3
      ;;
    del)
      python3 - "$CADDY_SITES" "$IP" <<'PY'
import sys, glob, re
sites, ip = sys.argv[1], sys.argv[2]
for f in glob.glob(sites + "/*.caddy"):
    s = open(f, encoding="utf-8", errors="surrogateescape").read()
    s = re.sub(r"(client_ip [^\n]*)\s+" + re.escape(ip) + r"\b", r"\1", s)
    open(f, "w", encoding="utf-8", errors="surrogateescape").write(s)
print("caddy: entri dihapus")
PY
      caddy validate --config /etc/caddy/Caddyfile >/dev/null 2>&1 && systemctl reload caddy && sleep 3
      ;;
    list)
      echo "== caddy =="; grep -h "@soc_block_ip client_ip" "$CADDY_SITES"/*.caddy 2>/dev/null | sort -u
      ;;
  esac
fi
