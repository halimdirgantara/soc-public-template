---
name: soc-local
description: >
  Use local SOC tools for Loki triage, SSH brute-force analysis, Laravel error
  investigation, Grafana alert follow-up, Fail2Ban checks, Promtail validation,
  and malware watch summaries.
---

# Skill: SOC Local Triage

## Purpose

Use this skill when the operator asks about:

- Loki logs or log queries
- Grafana alerts
- Laravel errors or production.ERROR events
- SSH brute-force or failed login spikes
- Nginx suspicious scan activity
- Fail2Ban jail status or bans
- Promtail service status
- UFW firewall status
- Malware watch results
- SOC incident triage and reporting

## Rules

- No real IP addresses, hostnames, tokens, or credentials in this file.
- Use `example-org` as the sanitised instance label.
- Replace `LOKI_SERVER_IP` and `GRAFANA_SERVER_IP` with production values in the private repo.
- Keep evidence separate from assumptions in all operator-facing responses.

## Environment

| Variable | Description |
|---|---|
| `SOC_LOKI_URL` | Loki base URL, e.g. `http://LOKI_SERVER_IP:3100` |
| `SOC_GRAFANA_URL` | Grafana base URL, e.g. `http://GRAFANA_SERVER_IP` |
| `SOC_INSTANSI` | Instance label used in Loki streams, e.g. `example-org` |

Common Loki stream labels: `instansi`, `host`, `server_ip`, `job`, `app`.

## Local Tools

Use these scripts when available on the Hermes node:

```bash
# Laravel error triage
~/soc-tools/loki-triage.sh "<host-regex>" "<app-regex>" "<range>"

# SSH brute-force triage
~/soc-tools/ssh-triage.sh "<host-regex>" "<range>"

# Malware watch summary
~/soc-tools/malware-watch-summary.sh "<app>"
```

Source scripts live in `scripts/soc-tools/` in this repository.

## Default Triage Workflow

1. Identify alert type: Laravel, SSH, Nginx, system, malware, or infrastructure.
2. Extract host, server_ip, app, time range, and severity from the alert.
3. Query Loki before drawing conclusions.
4. Summarise only evidence-backed findings.
5. Recommend a safe next action.
6. Do not modify firewall rules, ban IPs, delete files, stop services, or quarantine files without explicit operator approval.

## Safety Rules

- Defensive SOC use only.
- Preserve evidence before any containment action.
- For suspected malware: collect file paths, process IDs, network connections, hashes, and timestamps before acting.
- For SSH brute-force: check Fail2Ban status before recommending a UFW block.
- For Laravel errors: provide sample log lines, affected app, event count, and likely cause.
- Commands that require approval before execution: `ufw deny`, `fail2ban-client ... banip`, `rm`, `mv` to quarantine, `pkill`, `systemctl stop`, Nginx/PHP-FPM config changes.
