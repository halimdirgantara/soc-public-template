# VictoriaLogs LogsQL alert queries (default)
#
# Copy into Grafana alert rules (victoriametrics-logs-datasource) or
# into a watchdog script (e.g. the vl-monitor pattern used in production:
# poll /select/logsql/query every 5m, alert via Telegram bot).
#
# Syntax notes:
#   _time:5m            — last 5 minutes (no [5m] range vector needed)
#   _stream:{job="..."} — stream/label filter (like {job="..."} in LogQL)
#   _msg: "text"        — full-text match on message
#   ~"regex"            — regex match on message
#   ! "text"            — negative match
#   | limit N           — cap results

# SSH brute-force (per attacker IP, 5m)
#
# _time:5m _stream:{instansi="example-org", job="auth"} ~"(?i)(Failed password|Invalid user|authentication failure)" | extract "from <src_ip> " as src_ip | stats by (host, src_ip) count() hits | filter hits >= 5

# CrowdSec decision / ban (5m)
#
# _time:5m _stream:{instansi="example-org"} ~"crowdsecurity/.+|ban:1|Ip:.*ban|overflow" ! "component=" ! "whitelisted" | limit 20

# Nginx suspicious path (10m) — wp-login, phpmyadmin, .env, .git, /etc/passwd
#
# _time:10m _stream:{instansi="example-org", job=~"nginx.*"} ~"wp-login|phpmyadmin|\\.env|\\.git|/etc/passwd|cgi-bin|server-status" ! "scanner-user-agent" | limit 20

# UFW block spike (10m)
#
# _time:10m _stream:{instansi="example-org"} "UFW BLOCK" | stats by (host) count() hits | filter hits >= 10

# Laravel application errors (5m) — production.ERROR
#
# _time:5m _stream:{instansi="example-org", job="laravel"} "production.ERROR" ! "component=" | limit 10
