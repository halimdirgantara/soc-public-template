# VictoriaLogs — Default Log Store (Loki Replacement)

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
Promtail → VictoriaLogs (:9428) → Grafana (victoriametrics-logs-datasource plugin)
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
curl http://localhost:9428/health
curl 'http://localhost:9428/select/logsql/query' -d 'query=_time:5m _msg:* | limit 5'
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

## Promtail ingestion

VictoriaLogs accepts the Loki push protocol — point Promtail at the
**`/insert/loki/api/v1/push`** path (not `/api/v1/push`):

```yaml
clients:
  - url: http://YOUR_SERVER_IP:9428/insert/loki/api/v1/push
```

## Grafana datasource

Use the **`victoriametrics-logs-datasource`** plugin (for logs — the
`victoriametrics-datasource` plugin is for VictoriaMetrics metrics only).

```yaml
apiVersion: 1
datasources:
  - name: VictoriaLogs
    type: victoriametrics-logs-datasource
    access: proxy
    url: http://YOUR_SERVER_IP:9428
    isDefault: true
    jsonData:
      dataSourceType: victorialogs
```

## Migration from Loki

1. Install VictoriaLogs on the same host as previous Loki
2. Update Promtail client URL from `http://loki:3100/loki/api/v1/push` → `http://victorialogs:9428/insert/loki/api/v1/push`
3. Install `victoriametrics-logs-datasource` plugin in Grafana
4. Add VictoriaLogs as data source in Grafana (type: `victoriametrics-logs-datasource`, URL: `http://victorialogs:9428`)
5. Restart Promtail
6. Verify data flows: `curl 'http://localhost:9428/select/logsql/query' -d 'query=_time:5m _msg:* | limit 5'`

See `docs/07-migration-loki-to-victorialogs.md` for the full guide.

## Query examples (LogsQL)

```bash
# All logs last 5m
curl 'http://localhost:9428/select/logsql/query' -d 'query=_time:5m | limit 10'

# Auth failures
curl 'http://localhost:9428/select/logsql/query' -d 'query=_time:5m _stream:{job="auth"} ~"Failed password|Invalid user" | limit 10'

# By host
curl 'http://localhost:9428/select/logsql/query' -d 'query=_time:5m host="web-admin" | limit 10'

# Count by stream (stats)
curl 'http://localhost:9428/select/logsql/query' -d 'query=* | stats by (_stream) count() rows | limit 20'
```

## Troubleshooting

```bash
# Check if VictoriaLogs is running
curl -s http://localhost:9428/health

# Check memory usage
ps aux | grep victoria-logs | awk '{print $6/1024 " MB"}'

# Check ingested logs count
curl -s 'http://localhost:9428/select/logsql/query' -d 'query=* | stats count() rows'
```
