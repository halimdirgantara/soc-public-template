# PRD.public.md — Open SOC Deployment Template

## 1. Summary

This repository is a sanitized public template for building a lightweight open-source SOC deployment stack.

The stack includes Grafana, VictoriaLogs (default log store), Loki (legacy/rollback), Promtail, CrowdSec, CrowdSec Firewall Bouncer, Telegram alerting, Nginx reverse proxy examples, and Cloudflare notes.

This public repository must not contain production topology, real IP addresses, real hostnames, or secrets.

## 2. Goals

1. Build a repeatable open-source SOC baseline.
2. Centralize Linux, SSH, Nginx, UFW, and CrowdSec logs.
3. Create Grafana dashboards based on VictoriaLogs streams/labels (LogsQL).
4. Send alert notifications to Telegram.
5. Test CrowdSec and firewall bouncer safely.
6. Separate public templates from private production configuration.

## 3. Non-Goals

This repository does not provide:

- Production credentials.
- Production inventory.
- Enterprise SIEM replacement.
- Full incident response automation.
- Full Cloudflare account automation.
- Forensic malware analysis tooling.
- A guarantee that all templates are production-ready without tuning.

## 4. Public-Safe Data Rules

Allowed:

- Dummy IP addresses.
- Example domains.
- Generic LogsQL/LogQL queries.
- Generic Grafana dashboard templates.
- Example inventory.
- `.env.example`.
- Generic scripts and SOP documentation.

Not allowed:

- Real IP addresses.
- Real hostnames.
- Real Telegram token or chat ID.
- Real Cloudflare tunnel credentials.
- Real SSH username/password/private key.
- Real CrowdSec bouncer key.
- Real Grafana admin password.
- Production inventory.
- Screenshots showing sensitive data.

## 5. Target Architecture

```text
Application servers
  -> Promtail
  -> VictoriaLogs (:9428)
  -> Grafana dashboards and alerts (victoriametrics-logs-datasource)
  -> Telegram notification
```

Loki (:3100) is kept only as a rollback path — see `docs/07-migration-loki-to-victorialogs.md`.

Optional auto-remediation:

```text
Server logs
  -> CrowdSec parser and scenarios
  -> CrowdSec decisions
  -> Firewall bouncer
  -> iptables/ipset/nftables block
```

## 6. Standard Labels

```text
instansi="example-org"
host="<hostname>"
server_ip="<private_ip>"
job="<log_type>"
exposure_type="public_direct|reverse_proxy|internal"
environment="lab|staging|production"
```

> Note: the template uses `instansi` (the production label used by organisasi contoh SOC) instead of `org`. Adjust per deployment.

## 7. Functional Requirements

### FR-01 VictoriaLogs (default log store)

- Provide example VictoriaLogs configuration (`victorialogs/`).
- VictoriaLogs should expose `:9428`.
- `/health` must be testable.
- LogsQL query endpoint `/select/logsql/query` must be testable.
- Accept Promtail push at `/insert/loki/api/v1/push` (Loki-compatible).

### FR-02 Loki (legacy, rollback only)

- Keep example Loki configuration (`loki/`).
- Loki should expose `:3100`.
- `/ready` must be testable.
- `/loki/api/v1/labels` must be testable.

### FR-03 Grafana

- Provide VictoriaLogs datasource template (default) and Loki datasource template (legacy).
- Provide example dashboard provisioning.
- Provide alerting template placeholders (LogsQL + LogQL).
- Do not hardcode production URLs.

### FR-04 Promtail

- Provide Promtail config template.
- Provide mass deployment script template.
- Support auth, syslog, kern, native Nginx, and custom Nginx paths.
- Use labels consistently.

### FR-05 CrowdSec

- Provide acquisition examples.
- Support Linux auth/syslog.
- Support native Nginx.
- Support custom web panel Nginx logs.
- Provide bouncer test procedure.

### FR-06 Telegram Alert

- Provide contact point documentation.
- Store token/chat ID only via environment or local secret.
- No token should be committed.

## 8. Alert Templates

Core alerts (see `alerts/logsql/` for VictoriaLogs, `alerts/logql/` for Loki):

- SSH failed login per attacker.
- Nginx suspicious path.
- UFW block spike.
- CrowdSec decision or ban.
- Laravel application errors.

## 9. Acceptance Criteria

The public repo is acceptable if:

- It contains no real secrets.
- It contains no real production inventory.
- It uses only dummy IPs and domains.
- It contains reusable templates.
- It documents how to move from public template to private production repo.
- It includes `.gitignore`.
- It includes `.env.example`.
- It includes security warnings.

## 10. Roadmap

- Add GitHub Actions for markdown lint.
- Add YAML validation.
- Add ShellCheck.
- Add PSScriptAnalyzer.
- Add secret scanning.
- Add sample Grafana dashboards.
- Add sanitized Docker Compose examples.
