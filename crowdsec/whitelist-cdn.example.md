# CrowdSec — whitelist CDN & bot agar tidak salah blokir

Ketika trafik masuk melalui CDN/reverse proxy, CrowdSec dapat melihat IP CDN
sebagai sumber dan memicu alert massal. Tanpa whitelist, IP CDN bisa masuk
keputusan ban dan memutus pengguna sah.

## Pasang whitelist bawaan hub

```bash
cscli postoverflows install crowdsecurity/cdn-whitelist
cscli postoverflows install crowdsecurity/seo-bots-whitelist
systemctl reload crowdsec
cscli postoverflows list | grep -E "cdn-whitelist|seo-bots"
```

Keduanya dijalankan di **setiap host** yang menjalankan CrowdSec.

## Ban manual

```bash
cscli decisions add --ip <IP> --duration 24h --type ban --reason "manual SOC"
cscli decisions list --ip <IP>
cscli decisions delete --ip <IP>
```

## Penting: ban firewall tidak menembus CDN

`cs-firewall-bouncer` memeriksa IP paket TCP. Jika trafik datang dari CDN,
IP yang terlihat adalah IP CDN — ban terhadap IP penyerang **tidak akan cocok**.

Konsekuensinya:

| Jalur trafik | Yang efektif |
|---|---|
| Koneksi langsung ke origin | firewall bouncer / `cscli decisions` |
| Lewat CDN / tunnel | WAF di reverse proxy berbasis IP asli, atau WAF penyedia CDN |

Verifikasi: setelah ban, periksa log akses — bila request dari IP yang sama masih
masuk, berarti trafik melewati CDN dan ban di origin tidak berlaku.
