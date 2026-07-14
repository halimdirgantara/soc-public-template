# Migration Guide: Loki → VictoriaLogs

## Why Migrate?

| Resource | Loki (before) | VictoriaLogs (after) |
|----------|---------------|---------------------|
| RAM | 5.9 GB (OOM-prone) | ~14-200 MB |
| Disk | 4.8 GB (WAL) | Minimal |
| Restart required | Frequent (OOM) | Rare |
| Deployment | Complex config | 1 docker command |

## Step 1: Deploy VictoriaLogs

```bash
docker run -d --restart unless-stopped \
  --name victorialogs \
  -p 9428:9428 \
  -v /var/lib/victorialogs:/victoria-logs-data \
  victoriametrics/victoria-logs
```

Verify:
```bash
curl http://localhost:9428/api/v1/query -d 'query={_msg="*"}'
```

## Step 2: Install Grafana Plugin

```bash
# Download plugin (check latest release number)
wget https://github.com/VictoriaMetrics/victoriametrics-datasource/releases/download/v0.25.2/victoriametrics-datasource-v0.25.2.tar.gz

# Extract to Grafana plugins
tar -xzf victoriametrics-datasource-*.tar.gz
sudo mv victoriametrics-datasource /var/lib/grafana/plugins/

# Allow unsigned plugin
echo 'allow_loading_unsigned_plugins = victoriametrics-datasource' \
  | sudo tee -a /etc/grafana/grafana.ini

# Restart Grafana
sudo systemctl restart grafana-server
```

## Step 3: Add Datasource in Grafana

Via Grafana UI: Configuration → Data Sources → Add → "VictoriaMetrics"

- Name: `victorialogs`
- URL: `http://YOUR_SERVER_IP:9428`
- Type: `VictoriaLogs`

## Step 4: Update Promtail

Edit `/etc/promtail/promtail-config.yaml`:

```yaml
clients:
  # Send to VictoriaLogs instead of Loki
  - url: http://YOUR_SERVER_IP:9428/api/v1/push
```

Restart Promtail:
```bash
sudo systemctl restart promtail
```

## Step 5: Verify Data Flow

```bash
# Query VictoriaLogs for recent logs
curl -s 'http://localhost:9428/api/v1/query' \
  -d 'query={_msg="*"}'
  -d 'limit=5'

# Check Promtail logs for errors
journalctl -u promtail --no-pager -n 20 | tail
```

## Step 6: Migrate Alert Rules

In Grafana:
1. Create a **new copy** of each alert rule
2. Change the data source from `Loki` → `VictoriaLogs`
3. Test the new rule
4. Disable the old rule (keep for historical data query)

Query syntax differences:

| Loki (LogQL) | VictoriaLogs (LogsQL) |
|-------------|----------------------|
| `{job="syslog"} \|~ "error"` | `_msg: error AND _stream: {job="syslog"}` |
| `count_over_time({job="syslog"}[5m])` | `count(_msg) WHERE _time: 5m AND _stream: {job="syslog"}` |

> Note: LogsQL is **SQL-like** — write conditions as field=value pairs.

## Step 7: Decommission Loki (Optional)

After confirming VictoriaLogs works:

```bash
sudo systemctl stop loki
sudo systemctl disable loki
sudo rm -rf /var/lib/loki  # remove old data (WAL + chunks)
```

**Keep Loki data until VictoriaLogs is fully tested.**

## Troubleshooting

```bash
# No data in VictoriaLogs
curl -s 'http://localhost:9428/api/v1/query?query=_msg:*'

# Check Promtail connectivity
journalctl -u promtail --no-pager -n 30 | grep -i error

# Memory check
ps aux | grep victoria | awk '{print $6/1024 " MB"}'
```
