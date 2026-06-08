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
â”œâ”€â”€ inventory/
â”œâ”€â”€ grafana/
â”œâ”€â”€ loki/
â”œâ”€â”€ promtail/
â”œâ”€â”€ crowdsec/
â”œâ”€â”€ nginx/
â”œâ”€â”€ cloudflare/
â”œâ”€â”€ alerts/
â”œâ”€â”€ scripts/
â”œâ”€â”€ docs/
â””â”€â”€ skills/
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
9. Keep production values in a private repository.
