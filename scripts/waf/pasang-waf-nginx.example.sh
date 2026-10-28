#!/bin/bash
# Contoh pemasang WAF + real-IP untuk nginx.
# Idempotent, membuat backup, menguji konfigurasi, lalu reload.
#
# Pakai: sudo ./pasang-waf-nginx.example.sh [domain-uji]
#
# Sesuaikan NGINX_CONF/VHOST_DIR dengan layout distribusi Anda. Nilai bawaan
# mengikuti layout panel aaPanel; untuk distro biasa gunakan
#   NGINX_CONF=/etc/nginx/nginx.conf VHOST_DIR=/etc/nginx/conf.d
set -u

NGINX_CONF=${NGINX_CONF:-/www/server/nginx/conf/nginx.conf}
CONF_DIR=$(dirname "$NGINX_CONF")
VHOST_DIR=${VHOST_DIR:-/www/server/panel/vhost/nginx}
SRC=$(cd "$(dirname "$0")/../../nginx" && pwd)
TS=$(date +%Y%m%d-%H%M%S)
BK=/root/waf-backup-$TS
TESTHOST=${1:-}

[ -w "$CONF_DIR" ] || { echo "Tidak bisa menulis $CONF_DIR"; exit 1; }

mkdir -p "$BK/vhost"
cp -p "$NGINX_CONF" "$BK/nginx.conf"
cp -p "$VHOST_DIR"/*.conf "$BK/vhost/" 2>/dev/null

install -m 644 "$SRC/real-ip.example.conf"  "$CONF_DIR/cloudflare-realip.conf"
install -m 644 "$SRC/waf-traversal.example.conf" "$CONF_DIR/soc-waf-map.conf"
install -m 644 "$SRC/waf-rules.example.conf"     "$CONF_DIR/soc-waf-rules.conf"

python3 - "$NGINX_CONF" <<'PY'
import sys, re
p = sys.argv[1]
s = open(p, encoding="utf-8", errors="surrogateescape").read()
if "cloudflare-realip.conf" in s:
    print("include http sudah ada")
else:
    if re.search(r"include\s+mime\.types;", s):
        s = re.sub(r"(include\s+mime\.types;)", r"\1\n    include cloudflare-realip.conf;\n    include soc-waf-map.conf;", s, count=1)
    else:
        s = s.replace("http {", "http {\n    include cloudflare-realip.conf;\n    include soc-waf-map.conf;", 1)
    open(p, "w", encoding="utf-8", errors="surrogateescape").write(s)
    print("include http ditambahkan")
PY

python3 - "$VHOST_DIR" "$CONF_DIR" <<'PY'
import sys, glob, re
vdir, cdir = sys.argv[1], sys.argv[2]
ins = "    include %s/soc-waf-rules.conf;\n" % cdir
n = 0
for f in glob.glob(vdir + "/*.conf"):
    s = open(f, encoding="utf-8", errors="surrogateescape").read()
    if "soc-waf-rules.conf" in s:
        continue
    m = re.search(r"^\s*server\s*\{?\s*$", s, re.M)
    if not m:
        continue
    i = s.find("{", m.start())
    if i < 0:
        continue
    open(f, "w", encoding="utf-8", errors="surrogateescape").write(s[:i+1] + "\n" + ins + s[i+1:])
    n += 1
print("vhost disisipi aturan:", n)
PY

if ! nginx -t 2>&1 | tail -1; then
    echo "VALIDASI GAGAL — rollback"
    cp -p "$BK/nginx.conf" "$NGINX_CONF"
    cp -p "$BK/vhost"/*.conf "$VHOST_DIR"/ 2>/dev/null
    exit 1
fi

# Sebagian panel menjalankan nginx lewat init.d, bukan systemd.
systemctl reload nginx 2>/dev/null || /etc/init.d/nginx reload >/dev/null 2>&1 || nginx -s reload
sleep 3

if [ -n "$TESTHOST" ]; then
    echo "uji traversal : $(curl -sk -o /dev/null -m 8 -w '%{http_code}' -H "Host: $TESTHOST" 'https://127.0.0.1/?a=../') (harus 403)"
    echo "uji normal    : $(curl -sk -o /dev/null -m 8 -w '%{http_code}' -H "Host: $TESTHOST" 'https://127.0.0.1/')"
fi

echo "BACKUP=$BK"
