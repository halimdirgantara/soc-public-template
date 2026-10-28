# WAF ringan & blokir IP di origin (contoh)

Kumpulan contoh untuk tiga hal:

1. **Real client IP** di belakang CDN/reverse proxy (`nginx/real-ip.example.conf`).
2. **WAF traversal** — `403` untuk `../`, `%2e%2e`, `%00`, `/etc/passwd`
   (`nginx/waf-traversal.example.conf` + `nginx/waf-rules.example.conf`).
3. **Daftar blokir IP** berbasis IP asli, baik di nginx maupun Caddy.

## Skrip

| Skrip | Fungsi |
|---|---|
| `pasang-waf-nginx.example.sh` | pasang real-IP + WAF + include per-vhost (nginx) |
| `pasang-waf-caddy.example.sh` | `trusted_proxies` + aturan per-situs (Caddy ≥ 2.8) |
| `tambah-blokir-ip.example.sh` | `add` / `del` / `list` IP pada nginx & Caddy |
| `sebar-ban-crowdsec.example.sh` | sebar ban CrowdSec lokal atau armada |

## Jebakan yang sudah terbukti

- **Jangan** memakai `$http_cf_connecting_ip` untuk map blokir nginx — nilainya
  tidak terbaca saat `if` dievaluasi; gunakan `$remote_addr` (hasil `real_ip`).
- **Jangan** memakai `expression {http.request.client_ip}` di Caddy — gunakan
  matcher `client_ip`.
- Sebagian panel menjalankan nginx lewat `init.d`; `systemctl reload nginx` gagal
  dan harus difallback.
- Reload bersifat **asinkron** — beri jeda ±3 detik sebelum menguji, jika tidak
  hasil uji memakai konfigurasi lama.
- `trusted_proxies` Caddy butuh versi **≥ 2.7**; sertakan `127.0.0.1/32` bila ada
  tunnel lokal di depan Caddy.
- Ban CrowdSec di firewall **tidak** menahan trafik yang lewat CDN.

Runbook lengkap: `docs/runbook-waf-cloudflare-blocklist.public.md`.
