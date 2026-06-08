# Installation Guide

This guide is intentionally generic.

## Steps

1. Prepare a private inventory.
2. Deploy Loki.
3. Deploy Grafana.
4. Configure Grafana datasource.
5. Deploy Promtail agents.
6. Deploy CrowdSec on exposed servers.
7. Deploy firewall bouncer after whitelist review.
8. Configure Telegram alerts.
9. Validate logs and alerts.
10. Keep production values outside this public repository.

## Validation

```bash
curl http://10.0.0.10:3100/ready
curl http://10.0.0.10:3100/loki/api/v1/labels
```
