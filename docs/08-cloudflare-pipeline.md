# 08 — Pipeline Cloudflare: log → VictoriaLogs → Grafana → auto-ban

Dokumen ini merangkum alur yang dipakai di SOC: peristiwa WAF Cloudflare ditarik
berkala, disimpan di VictoriaLogs, divisualkan di Grafana, lalu dipakai untuk
memblokir otomatis dan mengirim notifikasi.

## Alur

```
Cloudflare (WAF, rate limit, bot fight)
        │  GraphQL firewallEventsAdaptive (retensi 30 hari pada paket Pro)
        ▼
cf-security-pull.py   (cron tiap 5 menit, read-only)
        │  stream job=cf-security, retensi VictoriaLogs 90 hari
        ▼
VictoriaLogs :9428 ──► Grafana (2 dashboard + 6 aturan alert)
        │
        ├──► vl-exporter :9101 ──► Prometheus (metrik untuk alert)
        └──► cf-autoban.py (cron 5 menit) ──► custom rule WAF "Auto-ban" 24 jam
                                             └──► notifikasi bot Telegram
```

## Komponen

| Berkas | Peran |
|---|---|
| `cloudflare/cf-security-pull.example.py` | tarik event → VL, dedupe SQLite |
| `cloudflare/cf-autoban.example.py` | IP dengan serangan berulang → blokir 24 jam |
| `cloudflare/vl-exporter.example.py` | metrik Prometheus + `/cf_events.json`, `/cf_stats.json` |
| `grafana/dashboards/soc-cloudflare-waf.example.json` | dashboard teknis (10 panel) |
| `grafana/dashboards/soc-panduan-awam.example.json` | dashboard awam (13 panel) |
| `grafana/provisioning/alerting/soc-cloudflare.example.yaml` | 6 aturan alert |
| `alerts/logsql/cloudflare-pipeline.example.logsql` | query siap pakai |

## Pemasangan

1. **Zona & token**
   ```bash
   export CF_ZONE_ID="<zone-id>"
   export CF_ZONE_NAME="example.go.id"
   export CF_API_TOKEN_FILE="$HOME/.cf-soc/token"   # isi: account_id|token, mode 600
   ```
   Token butuh izin: Zone Analytics Read, Zone WAF Read/Edit (untuk auto-ban),
   dan Zone Settings Read.

2. **Tarik event** (cron 5 menit)
   ```bash
   */5 * * * * VL_URL=http://10.0.0.30:9428 /opt/soc/cloudflare/cf-security-pull.py --quiet
   ```
   Uji manual: `--hours 24` untuk mengisi data sehari ke belakang.

3. **Retensi 90 hari** — jalankan VictoriaLogs dengan:
   ```
   -retentionPeriod=90d
   ```

4. **Dashboard** — impor JSON, lalu ganti placeholder:
   `YOUR_VICTORIALOGS_UID`, `YOUR_INFINITY_UID`, `YOUR_PROMETHEUS_UID`
   sesuai UID datasource di Grafana.

5. **Auto-ban**
   ```bash
   CF_ZONE_ID=... /opt/soc/cloudflare/cf-autoban.py \
       --threshold 50 --window 15 --hours 24 --quiet --notify
   ```
   - Ambang: **≥50 blokir dalam 15 menit**
   - Durasi: **24 jam**, maksimum 150 IP
   - Hanya IP luar negeri (default); IP dalam negeri butuh `--include-id`
   - Allowlist: `~/.cf-soc/allow.txt` (CIDR privat + IP pemantau)
   - Notifikasi memakai `~/.soc-bot/token` berisi `token|chat_id`

6. **Metrik & alert** — jalankan `vl-exporter` di `:9101`, arahkan Prometheus
   (`prometheus/prometheus.example.yml`), lalu aktifkan
   `soc-cloudflare.example.yaml`.

## Catatan operasional

- **Kuota paket Pro**: rate limiting hanya 2 aturan, dan `ip.geoip.country`
  tidak tersedia di rate limit → pakai custom rule + Managed Challenge.
- **Bot Fight Mode** memblokir pemanggilan server-ke-server tanpa User-Agent.
  Mitigasi: rule *Skip* untuk IP+host mitra, bukan mematikan bot mode global.
- **Pemantau** harus memakai UA khusus (contoh `SOC-Monitor/1.0`) agar tidak
  ikut diblokir.
- **Kegagalan pipeline** dideteksi lewat aturan `Pipeline_Stalled`
  (tidak ada event 30 menit).
- **Privasi**: kolom `clientRequestQuery` dapat memuat data sensitif; batasi
  akses dashboard dan retensi sesuai kebijakan instansi.
