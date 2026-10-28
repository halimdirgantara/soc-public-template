# Installation Guide

This guide is intentionally generic.

## Steps

1. Prepare a private inventory.
2. Deploy VictoriaLogs (default log store — low memory, Loki-compatible).
   - Use `victorialogs/docker-compose.example.yml` or see `victorialogs/README.md`.
3. Deploy Grafana.
4. Configure Grafana datasource:
   - `grafana/provisioning/datasources/victorialogs.example.yml` (default datasource)
   - Install `victoriametrics-logs-datasource` plugin (lihat docs/08-cloudflare-pipeline.md).
5. Deploy Promtail agents (`promtail/` — push to `VL_PUSH_URL`).
6. Deploy CrowdSec on exposed servers.
7. Deploy firewall bouncer after whitelist review.
8. Configure Telegram alerts.
9. Validate logs and alerts.
10. Keep production values outside this public repository.

## Validation

VictoriaLogs (default):

```bash
curl http://10.0.0.10:9428/select/logsql/query -d 'query=_time:5m _stream:{job="auth"} | limit 5'
curl http://10.0.0.10:9428/health
```

```
