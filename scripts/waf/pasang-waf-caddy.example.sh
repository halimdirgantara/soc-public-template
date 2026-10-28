#!/bin/bash
# Contoh pemasang WAF + real-IP untuk Caddy (>= 2.8).
# Menambahkan blok global trusted_proxies dan aturan per-situs.
#
# Pakai: sudo ./pasang-waf-caddy.example.sh [domain-uji]
set -u

CFG=${CFG:-/etc/caddy/Caddyfile}
SITES=${SITES:-/etc/caddy/sites}
TS=$(date +%Y%m%d-%H%M%S)
BK=/root/caddy-waf-$TS
TESTHOST=${1:-}

command -v caddy >/dev/null || { echo "caddy tidak ditemukan"; exit 1; }
mkdir -p "$BK/sites"
cp -p "$CFG" "$BK/Caddyfile"
cp -p "$SITES"/*.caddy "$BK/sites/" 2>/dev/null

python3 - "$CFG" <<'PY'
import sys
p = sys.argv[1]
s = open(p, encoding="utf-8", errors="surrogateescape").read()
if "trusted_proxies" in s:
    print("trusted_proxies sudah ada")
else:
    blok = """{
\tservers {
\t\ttrusted_proxies static 127.0.0.1/32 ::1/128 173.245.48.0/20 103.21.244.0/22 103.22.200.0/22 103.31.4.0/22 141.101.64.0/18 108.162.192.0/18 190.93.240.0/20 188.114.96.0/20 197.234.240.0/22 198.41.128.0/17 162.158.0.0/15 104.16.0.0/13 104.24.0.0/14 172.64.0.0/13 131.0.72.0/22 2400:cb00::/32 2606:4700::/32 2803:f800::/32 2405:b500::/32 2405:8100::/32 2a06:98c0::/29 2c0f:f248::/32
\t}
}

"""
    open(p, "w", encoding="utf-8", errors="surrogateescape").write(blok + s)
    print("trusted_proxies ditambahkan (loopback untuk tunnel lokal)")
PY

python3 - "$SITES" <<'PY'
import sys, glob
traversal = """\t# --- WAF: blokir traversal & null-byte ---
\t@soc_trav {
\t\texpression {http.request.uri.query}.contains("../") || {http.request.uri.query}.contains("..%2f") || {http.request.uri.query}.contains("%00") || {http.request.uri.path}.contains("/etc/passwd") || {http.request.uri.query}.contains("/etc/passwd")
\t}
\trespond @soc_trav 403

"""
blockip = """\t# --- Daftar blokir IP (IP asli dari CDN) ---
\t@soc_block_ip client_ip 203.0.113.10
\trespond @soc_block_ip 403

"""
n = 0
for f in glob.glob(sys.argv[1] + "/*.caddy"):
    s = open(f, encoding="utf-8", errors="surrogateescape").read()
    if "soc_trav" in s:
        continue
    i = s.find("{")
    if i < 0:
        continue
    open(f, "w", encoding="utf-8", errors="surrogateescape").write(s[:i+1] + "\n" + traversal + blockip + s[i+1:])
    n += 1
print("situs disisipi aturan:", n)
PY

if ! caddy validate --config "$CFG" 2>&1 | tail -1 | grep -q Valid; then
    echo "VALIDASI GAGAL — rollback"
    cp -p "$BK/Caddyfile" "$CFG"
    cp -p "$BK/sites"/*.caddy "$SITES"/ 2>/dev/null
    exit 1
fi

systemctl reload caddy
sleep 3

if [ -n "$TESTHOST" ]; then
    echo "uji traversal : $(curl -sk -o /dev/null -m 8 -w '%{http_code}' -H "Host: $TESTHOST" 'https://127.0.0.1/?a=../') (harus 403)"
    echo "uji normal    : $(curl -sk -o /dev/null -m 8 -w '%{http_code}' -H "Host: $TESTHOST" 'https://127.0.0.1/')"
fi

echo "BACKUP=$BK"
