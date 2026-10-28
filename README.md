# Open SOC Deployment Template

<img width="1024" height="572" alt="image" src="https://github.com/user-attachments/assets/5cf2f9de-4144-4c64-a3b1-bc12594b070b" />

A sanitized public template for deploying a lightweight open-source SOC stack.

This repository provides example configurations, scripts, alert templates, and operational documentation for:

- Grafana
- VictoriaLogs (default log store — low-memory Loki replacement)
- Promtail
- CrowdSec
- CrowdSec Firewall Bouncer
- Nginx reverse proxy
- Cloudflare Tunnel notes
- Cloudflare WAF event pipeline (pull, dashboards, alerts, auto-ban)
- Prometheus exporter for SOC metrics
- Telegram alerting
- Hermes Agent SOC triage tools

## Security Notice

This is a public-safe template. It intentionally uses dummy values such as:

- `10.0.0.10`
- `10.0.0.11`
- `203.0.113.10`
- `logs.example.org`
- `example-org`

Do not commit:

- Real private IP addresses
- Real public IP addresses
- Production hostnames
- Telegram bot tokens
- Cloudflare credentials
- SSH private keys
- Grafana admin passwords
- CrowdSec API keys
- Production inventories

## Recommended Repository Split

Use two repositories:

1. Public repository: sanitized templates, generic scripts, documentation, and examples.
2. Private repository: production inventory, real domains, real IP addresses, secrets references, and actual deployment state.

## Quick Start

```powershell
git clone https://github.com/YOUR-ORG/soc-public-template.git
cd soc-public-template
copy .env.example .env
```

Edit `.env` locally. Do not commit it.

## Folder Structure

```text
.
├── inventory/
├── grafana/
│   ├── dashboards/          # contoh dashboard: teknis & panduan awam
│   └── provisioning/        # datasource + aturan alert
├── victorialogs/            # log store (retensi 90d)
├── prometheus/              # contoh scrape config
├── promtail/
├── crowdsec/
├── nginx/                   # real-IP, WAF traversal, contoh aturan blokir
├── cloudflare/              # pipeline: pull, auto-ban, exporter
├── alerts/
│   └── logsql/              # query VictoriaLogs (termasuk pipeline Cloudflare)
├── scripts/
│   ├── soc-tools/           # Hermes triage scripts
│   └── waf/                 # pemasang WAF + blokir IP (nginx & Caddy)
├── docs/
└── skills/
    └── 08-hermes-soc-local/ # Local SOC triage skill for Hermes
```

## Main Workflow

1. Prepare inventory using `inventory/hosts.example.csv`.
2. Deploy VictoriaLogs (`victorialogs/`, retensi 90 hari).
3. Deploy Grafana and configure the VictoriaLogs datasource (`victoriametrics-logs-datasource` plugin).
4. Deploy Promtail agents (push to `VL_PUSH_URL`, e.g. `http://<vl>:9428/insert/loki/api/v1/push`).
5. Deploy CrowdSec on exposed servers.
6. Deploy firewall bouncer after whitelist review.
7. Configure Telegram alerting.
8. Import dashboards and alert rules from `grafana/`; ganti placeholder UID datasource.
9. Jalankan pipeline Cloudflare: `cloudflare/cf-security-pull.example.py` (cron 5 menit),
   lalu `cf-autoban.example.py` untuk blokir otomatis.
10. Arahkan Prometheus ke `cloudflare/vl-exporter.example.py` (lihat `prometheus/`).
11. Deploy Hermes Agent and SOC triage tools — see `docs/06-hermes-soc-tools-triage.md`.
12. Keep production values in a private repository.

## Documentation

| File | Description |
|---|---|
| `docs/01-installation.md` | Core stack installation |
| `docs/02-telegram-alerting.md` | Telegram alert setup |
| `docs/03-troubleshooting.md` | Common issues |
| `docs/04-make-scripts-executable.md` | Script permissions |
| `docs/05-fail2ban-hermes-prep.md` | Fail2Ban hardening and Hermes node prep |
| `docs/06-hermes-soc-tools-triage.md` | Hermes Agent, SOC triage tools, local skills |
| `docs/08-cloudflare-pipeline.md` | Pipeline Cloudflare: tarik event, dashboard, alert, auto-ban |
| `docs/runbook-waf-cloudflare-blocklist.public.md` | WAF traversal, real-IP CDN, blokir IP di origin |

## Skills

| Skill | Description |
|---|---|
| `skills/00-soc-architecture-governance` | SOC architecture and governance |
| `skills/01-grafana-victorialogs` | Grafana and VictoriaLogs configuration |
| `skills/02-promtail-mass-deploy` | Promtail mass deployment |
| `skills/03-crowdsec-firewall-bouncer` | CrowdSec and firewall bouncer |
| `skills/04-telegram-alerting` | Telegram alerting |
| `skills/05-cloudflare-nginx-real-ip` | Cloudflare and Nginx real IP |
| `skills/06-operations-backup-audit` | Operations and backup audit |
| `skills/07-security-hardening` | Security hardening |
| `skills/08-hermes-soc-local` | Local SOC triage skill for Hermes |
