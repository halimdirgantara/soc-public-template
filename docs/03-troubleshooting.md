# Troubleshooting

## Loki ready but Grafana fails

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

## CrowdSec not parsing web logs

Check acquisition paths and run:

```bash
sudo cscli metrics
```

## Telegram spam

Set No Data to `Normal/OK`, group by useful labels, and increase thresholds.
