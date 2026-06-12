# Open SOC Deployment Template

<img width="1448" height="1086" alt="image" src="https://github.com/user-attachments/assets/6f4253c5-da47-4f68-a2e5-069f6b5b4d7d" />

A sanitized public template for deploying a lightweight open-source SOC stack.

This repository provides example configurations, scripts, LogQL alert templates, and operational documentation for:

- Grafana
- Loki
- Promtail
- CrowdSec
- CrowdSec Firewall Bouncer
- Nginx reverse proxy
- Cloudflare Tunnel notes
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
git clone https://github.com/YOUR-ORG/open-soc-template.git
cd open-soc-template
copy .env.example .env
```

Edit `.env` locally. Do not commit it.

## Folder Structure

```text
.
├── inventory/
├── grafana/
├── loki/
├── promtail/
├── crowdsec/
├── nginx/
├── cloudflare/
├── alerts/
├── scripts/
│   └── soc-tools/           # Hermes triage scripts
├── docs/
└── skills/
    └── 08-hermes-soc-local/ # Local SOC triage skill for Hermes
```

## Main Workflow

1. Prepare inventory using `inventory/hosts.example.csv`.
2. Deploy Loki.
3. Deploy Grafana and configure Loki datasource.
4. Deploy Promtail agents.
5. Deploy CrowdSec on exposed servers.
6. Deploy firewall bouncer after whitelist review.
7. Configure Telegram alerting.
8. Review dashboards and alert thresholds.
9. Deploy Hermes Agent and SOC triage tools — see `docs/06-hermes-soc-tools-triage.md`.
10. Keep production values in a private repository.

## Documentation

| File | Description |
|---|---|
| `docs/01-installation.md` | Core stack installation |
| `docs/02-telegram-alerting.md` | Telegram alert setup |
| `docs/03-troubleshooting.md` | Common issues |
| `docs/04-make-scripts-executable.md` | Script permissions |
| `docs/05-fail2ban-hermes-prep.md` | Fail2Ban hardening and Hermes node prep |
| `docs/06-hermes-soc-tools-triage.md` | Hermes Agent, SOC triage tools, local skills |

## Skills

| Skill | Description |
|---|---|
| `skills/00-soc-architecture-governance` | SOC architecture and governance |
| `skills/01-grafana-loki` | Grafana and Loki configuration |
| `skills/02-promtail-mass-deploy` | Promtail mass deployment |
| `skills/03-crowdsec-firewall-bouncer` | CrowdSec and firewall bouncer |
| `skills/04-telegram-alerting` | Telegram alerting |
| `skills/05-cloudflare-nginx-real-ip` | Cloudflare and Nginx real IP |
| `skills/06-operations-backup-audit` | Operations and backup audit |
| `skills/07-security-hardening` | Security hardening |
| `skills/08-hermes-soc-local` | Local SOC triage skill for Hermes |
