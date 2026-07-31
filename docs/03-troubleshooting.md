# Troubleshooting

## VictoriaLogs ready but Grafana fails

Use base URL as datasource (no path suffix):

```text
http://10.0.0.10:9428
```

Do not use:

```text
/health
/select/logsql/query
/insert/loki/api/v1/push
```

Make sure Grafana has the `victoriametrics-logs-datasource` plugin installed
(see `docs/07-migration-loki-to-victorialogs.md` step 2).

## Loki (legacy) ready but Grafana fails

Use base URL as datasource:

```text
http://10.0.0.10:3100
```

Do not use:

```text
/ready
/loki/api/v1/push
```

## Promtail not sending logs

```bash
sudo journalctl -u promtail --since "30 minutes ago" --no-pager
```

Look for:

```text
permission denied
connection refused
timeout
no such file
server returned
```

Verify the push URL matches VictoriaLogs' Loki-compatible endpoint:

```text
http://10.0.0.10:9428/insert/loki/api/v1/push
```

## No data in VictoriaLogs

```bash
curl -s 'http://10.0.0.10:9428/select/logsql/query' \
  -d 'query=_time:5m _msg:* | limit 5'
```

## CrowdSec not parsing web logs

Check acquisition paths and run:

```bash
sudo cscli metrics
```

## Telegram spam

Set No Data to `Normal/OK`, group by useful labels, and increase thresholds.
