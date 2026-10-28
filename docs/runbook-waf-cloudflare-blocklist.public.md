# Runbook publik — WAF traversal, real-IP CDN, dan blokir IP di origin

Dokumen ini merangkum pelajaran dari penerapan nyata pada stack SOC ringan
(nginx + Caddy + CrowdSec) yang seluruh trafik webnya melewati CDN.

Semua nama host, IP, dan domain di sini adalah **placeholder** (`<host>`,
`203.0.113.10`, `example.go.id`) sesuai RFC 5737/2606.

---

## 1. Masalah

Ketika trafik masuk melalui CDN/reverse proxy:

| Gejala | Sebab |
|---|---|
| Log akses mencatat IP CDN, bukan IP pengunjung | `real_ip_header` belum dipasang |
| Ban CrowdSec tidak menghentikan penyerang | firewall bouncer memeriksa IP paket = IP CDN |
| Pemindai tetap mengirim payload setelah di-ban | trafik melewati CDN, ban di origin tidak berlaku |
| `systemctl reload nginx` gagal di sebagian panel | layanan dijalankan lewat `init.d` |
| Hasil uji konfigurasi terbalik | reload bersifat asinkron |

**Kesimpulan:** pemblokiran harus dilakukan pada **IP asli** di reverse proxy,
atau di WAF penyedia CDN — bukan hanya di firewall origin.

---

## 2. Real client IP

nginx (`nginx/real-ip.example.conf`):

```nginx
set_real_ip_from 203.0.113.0/24;   # ganti dengan rentang CDN Anda
real_ip_header CF-Connecting-IP;   # atau X-Forwarded-For
```

Caddy ≥ 2.8 (blok global di `Caddyfile`):

```
{
    servers {
        trusted_proxies static 127.0.0.1/32 ::1/128 <rentang CDN>
    }
}
```

`127.0.0.1/32` diperlukan bila di depan Caddy ada tunnel lokal.

**Verifikasi:** kirim request dengan User-Agent unik, lalu pastikan log
menampilkan IP publik Anda. Di Caddy, field yang benar adalah `client_ip`
(`remote_ip` tetap `127.0.0.1`).

---

## 3. WAF traversal

nginx — map di `http{}`:

```nginx
map $args $soc_bad_args {
    default 0;
    "~*(\.\.|%2e%2e)(/|%2f)|%00|/etc/passwd|/proc/self|win\.ini|boot\.ini|%252e" 1;
}
```

dan aturan di tiap `server{}`:

```nginx
if ($soc_bad_args) { return 403; }
if ($soc_block_ip) { return 403; }
```

Caddy — per situs:

```
@soc_trav {
    expression {http.request.uri.query}.contains("../") || {http.request.uri.query}.contains("..%2f") || {http.request.uri.query}.contains("%00") || {http.request.uri.path}.contains("/etc/passwd") || {http.request.uri.query}.contains("/etc/passwd")
}
respond @soc_trav 403
```

Uji yang harus lolos:

| Payload | Harapan |
|---|---|
| `?a=../` | 403 |
| `?a=..%2f` | 403 |
| `?a=%00` | 403 |
| `?a=/etc/passwd` | 403 |
| `?a=teks-biasa` | 200/302 |

Batasan: **double-encode** (`..%252f`) tidak tertangkap; jangan menggantungkan
seluruh proteksi pada aturan ini.

---

## 4. Daftar blokir IP

nginx — gunakan `$remote_addr` (sudah ditulis ulang oleh `real_ip`):

```nginx
map $remote_addr $soc_block_ip {
    default 0;
    203.0.113.10 1;
}
```

Caddy ≥ 2.8 — matcher khusus:

```
@soc_block_ip client_ip 203.0.113.10
respond @soc_block_ip 403
```

**Cara menguji tanpa menyerang diri sendiri:** tambahkan sementara `127.0.0.1`
ke daftar → reload → harus `403` → hapus → harus normal kembali.

> Reload asinkron: beri jeda ±3 detik. Tanpa jeda, hasil uji bisa terbalik.

---

## 5. CrowdSec

Whitelist CDN wajib agar IP CDN tidak pernah masuk keputusan ban:

```bash
cscli postoverflows install crowdsecurity/cdn-whitelist
cscli postoverflows install crowdsecurity/seo-bots-whitelist
systemctl reload crowdsec
```

Ban manual dan penyebaran armada: `scripts/waf/sebar-ban-crowdsec.example.sh`.

Ingat tabel efektivitas:

| Jalur trafik | Yang efektif |
|---|---|
| Langsung ke origin | firewall bouncer |
| Lewat CDN/tunnel | WAF reverse proxy (IP asli) atau WAF CDN |

---

## 6. Rollback

| Perubahan | Rollback |
|---|---|
| nginx | pulihkan backup `nginx.conf` + `vhost/*.conf`, lalu reload |
| Caddy | pulihkan backup `Caddyfile` + `sites/*.caddy`, lalu reload |
| CrowdSec | `cscli decisions delete --ip <IP>` |

Skrip pemasang membuat backup otomatis ke `/root/...-<timestamp>/`.

---

## 7. Ringkasan pelajaran

1. Firewall bouncer buta terhadap trafik CDN — ban di origin tidak menutup serangan.
2. `$remote_addr` setelah `real_ip` adalah kunci nginx, bukan header mentah.
3. Caddy memakai matcher `client_ip`, bukan ekspresi placeholder.
4. Reload asinkron → selalu beri jeda sebelum menyimpulkan hasil uji.
5. Uji blokir dengan loopback sementara, jangan menunggu penyerang berikutnya.
6. Catat rollback sebelum mengubah konfigurasi produksi.
