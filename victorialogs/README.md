# VictoriaLogs — Alternative to Loki (Low Memory)

VictoriaLogs is a **drop-in replacement for Loki** designed for environments with limited RAM.  
Memory usage: **~14 MB** vs Loki's **5–6 GB** for the same log volume.

## Why VictoriaLogs?

| Metric | Loki | VictoriaLogs |
|--------|------|--------------|
| RAM idle | ~1 GB | ~14 MB |
| RAM under load | 5–6 GB (OOM-prone) | ~200 MB |
| Storage | TSDB + chunks | Structured log files |
| Query language | LogQL | LogsQL (SQL-like) |

## Architecture

```
Promtail → VictoriaLogs (:9428) → Grafana (victoriametrics-datasource plugin)
```

### Ports
- **9428** — HTTP API (push + query)
- **8429** — Metrics (Prometheus)

## Quick Start

```bash
# Pull and run
docker run -d --restart unless-stopped \
  --name victorialogs \
  --user "$(id -u):$(id -g)" \
  -p 9428:9428 \
  -v /var/lib/victorialogs:/victoria-logs-data \
  victoriametrics/victoria-logs

# Verify
curl http://localhost:9428/api/v1/query -d 'query={_msg="*"}'
```

## Persistent storage

```yaml
# docker-compose.yml
services:
  victorialogs:
    image: victoriametrics/victoria-logs
    restart: unless-stopped
    user: "1000:1000"
    ports:
      - "9428:9428"
    volumes:
      - /var/lib/victorialogs:/victoria-logs-data
      - ./victorialogs-config.yml:/etc/victorialogs/config.yml:ro
    command:
      - -storageDataPath=/victoria-logs-data
      - -httpListenAddr=:9428
      - -memory.allowedPercent=20
```

## Memory tuning

In low-RAM servers (< 2 GB):

```yaml
command:
  - -storageDataPath=/victoria-logs-data
  - -httpListenAddr=:9428
  - -memory.allowedPercent=15  # limit to 15% of total RAM
  - -logNewStreams=false         # reduce in-memory stream tracking
```

## Migration from Loki

1. Install VictoriaLogs on the same host as previous Loki
2. Update Promtail client URL from `http://loki:3100/loki/api/v1/push` → `http://victorialogs:9428/api/v1/push`
3. Install `victoriametrics-datasource` plugin in Grafana
4. Add VictoriaLogs as data source in Grafana (type: `victoriametrics-datasource`, URL: `http://victorialogs:9428`)
5. Restart Promtail
6. Verify data flows: `curl http://localhost:9428/api/v1/query -d 'query={_msg="*test*"}'`

## Grafana Alerts with VictoriaLogs

Alert rules written in LogQL work with VictoriaLogs' LogsQL.  
Update your Loki data source to point to VictoriaLogs instead, or create a separate data source.

**Migration path:**
1. Create new datasource for VictoriaLogs in Grafana
2. Duplicate alert rules, swapping data source to VictoriaLogs
3. Test rules, then decommission Loki

## Troubleshooting

```bash
# Check if VictoriaLogs is running
curl -s http://localhost:9428/api/v1/query -d 'query={_msg="*"}'

# Check memory usage
ps aux | grep victoria-logs | awk '{print $6/1024 " MB"}'

# Check ingested logs count
curl -s 'http://localhost:9428/api/v1/series?match[]={}'
```
