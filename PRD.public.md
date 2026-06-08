# PRD.public.md â€” Open SOC Deployment Template

## 1. Summary

This repository is a sanitized public template for building a lightweight open-source SOC deployment stack.

The stack includes Grafana, Loki, Promtail, CrowdSec, CrowdSec Firewall Bouncer, Telegram alerting, Nginx reverse proxy examples, and Cloudflare notes.

This public repository must not contain production topology, real IP addresses, real hostnames, or secrets.

## 2. Goals

1. Build a repeatable open-source SOC baseline.
2. Centralize Linux, SSH, Nginx, UFW, and CrowdSec logs.
3. Create Grafana dashboards based on Loki labels.
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
- Generic LogQL queries.
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
  -> Loki
  -> Grafana dashboards and alerts
  -> Telegram notification
```

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
org="example-org"
host="<hostname>"
server_ip="<private_ip>"
job="<log_type>"
exposure_type="public_direct|reverse_proxy|internal"
environment="lab|staging|production"
```

## 7. Functional Requirements

### FR-01 Loki

- Provide example Loki configuration.
- Loki should expose `:3100`.
- `/ready` must be testable.
- `/loki/api/v1/labels` must be testable.

### FR-02 Grafana

- Provide Loki datasource template.
- Provide example dashboard provisioning.
- Provide alerting template placeholders.
- Do not hardcode production URLs.

### FR-03 Promtail

- Provide Promtail config template.
- Provide mass deployment script template.
- Support auth, syslog, kern, native Nginx, and custom Nginx paths.
- Use labels consistently.

### FR-04 CrowdSec

- Provide acquisition examples.
- Support Linux auth/syslog.
- Support native Nginx.
- Support custom web panel Nginx logs.
- Provide bouncer test procedure.

### FR-05 Telegram Alert

- Provide contact point documentation.
- Store token/chat ID only via environment or local secret.
- No token should be committed.

## 8. Alert Templates

Core alerts:

- SSH failed login per attacker.
- Nginx suspicious path.
- UFW block spike.
- CrowdSec decision or ban.

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
