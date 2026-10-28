#!/usr/bin/env python3
"""VL metrics exporter for Prometheus - query VL HTTP API, expose as metrics"""
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.request
import os
import json
import time
import re

VL_URL = os.environ.get("VL_URL", "http://10.0.0.30:9428")

# Cache metrics
cache = {}
cache_time = 0
TTL = 10

QUERIES = {
    "vl_logs_total": "_time:5m instansi:example-org | stats count() as value",
    "vl_ufw_blocks": '_time:5m instansi:example-org AND "UFW BLOCK" | stats count() as value',
    "vl_failed_logins": '_time:5m instansi:example-org AND "Failed password" | stats count() as value',
    "vl_logs_by_host": "_time:5m instansi:example-org | stats by (host) count() as value | sort by (value) desc | limit 20",
    "vl_nginx_requests": "_time:5m job:nginx | stats count() as value",
    "vl_syslog_entries": "_time:5m job:syslog | stats count() as value",
    "vl_crowdsec_alerts": '_time:5m instansi:example-org AND _msg:~"(?i)crowdsec|decision|ban|alert|overflow" | stats count() as value',
    # --- Metrik per-aturan SOC -------------------------------------------------
    # Dipakai aturan alert Grafana lewat datasource *Prometheus* (format "wide"),
    # karena plugin victorialogs mengembalikan format "long" yang ditolak mesin
    # alert Grafana ("input data must be a wide series but got type long").
    # Catatan LogsQL: JANGAN memakai backslash di dalam regex `~"..."` (ditolak
    # dengan "compound token cannot start with \"). Pakai titik (.) sebagai
    # pengganti, atau frasa literal.
    "vl_rule_ssh_bruteforce": '_time:5m instansi:example-org AND job:auth AND _msg:~"(?i)(Failed password|Invalid user)" | stats count() as value',
    "vl_rule_ssh_failed_login": '_time:5m instansi:example-org AND job:auth AND _msg:~"Failed password" | stats count() as value',
    "vl_rule_ufw_block": '_time:5m instansi:example-org AND "UFW BLOCK" | stats count() as value',
    "vl_rule_crowdsec_alert": '_time:5m instansi:example-org AND _msg:~"crowdsecurity/" ! "component=" ! "whitelisted" | stats count() as value',
    "vl_rule_crowdsec_ban": '_time:5m instansi:example-org AND _msg:~"ban:1|Ip:.*ban|decision.*ban|Action.*ban" ! "component=" ! "community-blocklist" ! "/select/logsql/query" | stats count() as value',
    "vl_rule_cryptominer": '_time:5m instansi:example-org AND job:syslog AND _msg:~"(?i)(MoneroOcean|xmrig|contain-xmrig|cryptonight)" ! "component=" ! "query=" ! "rule_uid=" | stats count() as value',
    "vl_rule_webshell": '_time:5m instansi:example-org AND job:syslog AND "WARNING: Executable PHP-like files found in Laravel storage" ! "component=" ! "query=" | stats count() as value',
    "vl_rule_tempfile": '_time:5m instansi:example-org AND job:syslog AND "WARNING: Executable files found in temp directories" ! "component=" ! "query=" | stats count() as value',
    "vl_rule_persistence": '_time:5m instansi:example-org AND job:syslog AND _msg:~"(?i)(sysvsd|Known persistence file|systemd-private)" ! "component=" ! "query=" | stats count() as value',
    "vl_rule_cron": '_time:5m instansi:example-org AND job:auth AND _msg:~"CRON.*CMD" !~"(smmsp|root.*sessionclean|root.*cron.hourly|root.*run-parts)" | stats count() as value',
    "vl_rule_malware_critical": '_time:5m instansi:example-org AND job:syslog AND "CRITICAL: Malware indicators found" ! "component=" ! "query=" | stats count() as value',
    "vl_rule_nginx_suspicious": '_time:5m instansi:example-org AND job:nginx-access AND _msg:~"(wp-login|phpmyadmin|.env|.git|/etc/passwd|cgi-bin|server-status)" ! "component=" ! "query=" | stats count() as value',
    "vl_rule_laravel_error": '_time:5m instansi:example-org AND _msg:~"(production|local).(ERROR|CRITICAL)" ! "component=" ! "query=" ! "vl-monitor" | stats count() as value',
    # --- auditd (kernel-level) ---
    "vl_rule_audit_tmp_exec": '_time:5m instansi:example-org AND job:audit AND "soc_tmp_exec" AND "success=yes" | stats count() as value',
    "vl_rule_audit_www_exec": '_time:5m instansi:example-org AND job:audit AND "soc_www_exec" AND "success=yes" | stats count() as value',
    "vl_rule_audit_www_shell": '_time:5m instansi:example-org AND job:audit AND "soc_www_exec" AND _msg:~"comm=\"(bash|sh|dash)\"" AND "success=yes" | stats count() as value',
    "vl_rule_audit_www_download": '_time:5m instansi:example-org AND job:audit AND "soc_www_exec" AND _msg:~"comm=\"(curl|wget|nc|ncat|socat|perl|base64|python3)\"" AND "success=yes" | stats count() as value',
    "vl_rule_audit_identity": '_time:5m instansi:example-org AND job:audit AND _msg:~"soc_(identity|cron|ssh|systemd)" ! "CONFIG_CHANGE" ! _msg:~"(?i)(cpanel|setupipaliases)" | stats count() as value',
    "vl_rule_audit_shell": '_time:5m instansi:example-org AND job:audit AND "soc_shell" AND "success=yes" | stats count() as value',
    # --- Cloudflare Security Events (pipeline cf_security_pull.py) ---
    "vl_rule_cf_block": '_time:5m job:cf-security action:block | stats count() as value',
    "vl_rule_cf_429": '_time:5m job:cf-security status:429 | stats count() as value',
    "vl_rule_cf_challenge": '_time:5m job:cf-security action:managed_challenge | stats count() as value',
    "vl_rule_cf_sensitive": '_time:5m job:cf-security action:block AND _msg:~"(cgi-bin|.env|.git|etc/passwd|wp-login|phpmyadmin)" | stats count() as value',
    "vl_rule_cf_events_15m": '_time:15m job:cf-security | stats count() as value',
    "vl_rule_cf_topip": '_time:10m job:cf-security action:block | stats by (ip) count() as value | sort by (value) desc | limit 1',
}

# Metrik bernilai tunggal yang diterbitkan ke /metrics (tanpa pelabelan)
SINGLE = [
    "vl_logs_total", "vl_ufw_blocks", "vl_failed_logins", "vl_nginx_requests",
    "vl_syslog_entries", "vl_crowdsec_alerts",
    "vl_rule_ssh_bruteforce", "vl_rule_ssh_failed_login", "vl_rule_ufw_block",
    "vl_rule_crowdsec_alert", "vl_rule_crowdsec_ban", "vl_rule_cryptominer",
    "vl_rule_webshell", "vl_rule_tempfile", "vl_rule_persistence",
    "vl_rule_cron", "vl_rule_malware_critical", "vl_rule_nginx_suspicious",
    "vl_rule_laravel_error",
    "vl_rule_audit_tmp_exec", "vl_rule_audit_www_exec",
    "vl_rule_audit_www_shell",
    "vl_rule_audit_www_download",
    "vl_rule_audit_identity", "vl_rule_audit_shell",
    "vl_rule_cf_block", "vl_rule_cf_429", "vl_rule_cf_challenge",
    "vl_rule_cf_sensitive", "vl_rule_cf_events_15m", "vl_rule_cf_topip",
]


def query_vl(logsql):
    url = f"{VL_URL}/select/logsql/query?query={urllib.request.quote(logsql)}"
    try:
        with urllib.request.urlopen(url, timeout=5) as r:
            data = r.read().decode()
            lines = data.strip().split("\n")
            results = [json.loads(l) for l in lines if l]
            return results
    except Exception:
        return []


def update_cache():
    global cache, cache_time
    now = time.time()
    if now - cache_time < TTL:
        return
    for name, logsql in QUERIES.items():
        results = query_vl(logsql)
        cache[name] = results
    cache_time = now


def format_metric(name, labels, value):
    labels_str = ",".join(f'{k}="{v}"' for k, v in labels.items())
    return f'{name}{{{labels_str}}} {value}'


def kategori_serangan(rule, path):
    """Terjemahkan nama rule teknis menjadi jenis serangan yang mudah dipahami."""
    t = f"{rule or ''} {path or ''}".lower()
    if any(k in t for k in (".env", ".git", "passwd", "sensitive", "backup", "config", "secret")):
        return "Mencari file rahasia"
    if any(k in t for k in ("wp-", "wordpress", "xmlrpc", "joomla", "drupal", "cms")):
        return "Menyerang CMS/WordPress"
    if any(k in t for k in ("cgi-bin", "shell", "cmd", "/bin/sh", "traversal", "../")):
        return "Mencoba masuk ke server"
    if any(k in t for k in ("scanner", "attacker", "block attacker")):
        return "Pemindai otomatis"
    if "bot" in t:
        return "Bot otomatis"
    return "Serangan umum"


def aksi_indonesia(action, status):
    a = (action or "").lower()
    if a == "block":
        return "Dibatasi" if str(status) == "429" else "Diblokir"
    if "challenge" in a:
        return "Diverifikasi"
    if a in ("allow", "skip"):
        return "Diizinkan"
    return a or "-"


def ambil_event(limit=100):
    """Ambil event Cloudflare terbaru dari VictoriaLogs, sudah dalam bahasa Indonesia."""
    q = f"job:cf-security | sort by (_time) desc | limit {limit}"
    rows = query_vl(q)
    out = []
    for r in rows:
        out.append({
            "waktu": r.get("_time", ""),
            "tindakan": aksi_indonesia(r.get("action"), r.get("status")),
            "jenis": kategori_serangan(r.get("rule_name"), r.get("path")),
            "ip": r.get("ip", ""),
            "negara": r.get("country", ""),
            "situs": r.get("host", ""),
            "target": r.get("path", ""),
            "aturan": r.get("rule_name", ""),
        })
    return out



_stats_cache = {}


def ambil_statistik(kind, limit=10):
    """Agregat siap-pakai untuk panel Grafana (dipakai lewat datasource Infinity)."""
    import time as _t
    key = (kind, limit)
    now = _t.time()
    c = _stats_cache.get(key)
    if c and now - c[0] < 25:
        return c[1]
    if kind == "hourly":
        q = ("job:cf-security action:block | stats by (_time:1h) count() as jumlah "
             "| sort by (_time)")
    elif kind == "ip":
        q = (f"job:cf-security action:block | stats by (ip, country) count() as jumlah "
             f"| sort by (jumlah) desc | limit {limit}")
    elif kind == "rule":
        q = (f"job:cf-security action:block | stats by (rule_name) count() as jumlah "
             f"| sort by (jumlah) desc | limit {limit}")
    elif kind == "path":
        q = (f"job:cf-security action:block | stats by (path) count() as jumlah "
             f"| sort by (jumlah) desc | limit {limit}")
    elif kind == "host":
        q = (f"job:cf-security action:block | stats by (host) count() as jumlah "
             f"| sort by (jumlah) desc | limit {limit}")
    else:
        return []

    rows = query_vl(q)
    out = []
    for r in rows:
        if kind == "hourly":
            out.append({"waktu": r.get("_time", ""), "jumlah": int(float(r.get("jumlah", 0) or 0))})
        elif kind == "ip":
            out.append({"ip": r.get("ip", ""), "negara": r.get("country", ""),
                        "jumlah": int(float(r.get("jumlah", 0) or 0))})
        elif kind == "rule":
            nm = r.get("rule_name", "")
            out.append({"jenis": kategori_serangan(nm, ""), "aturan": nm,
                        "jumlah": int(float(r.get("jumlah", 0) or 0))})
        elif kind == "path":
            out.append({"target": r.get("path", ""), "jumlah": int(float(r.get("jumlah", 0) or 0))})
        elif kind == "host":
            out.append({"situs": r.get("host", ""), "jumlah": int(float(r.get("jumlah", 0) or 0))})
    _stats_cache[key] = (now, out)
    return out


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        update_cache()
        now = int(time.time())

        if self.path.startswith("/cf_stats.json"):
            from urllib.parse import urlparse, parse_qs
            qs = parse_qs(urlparse(self.path).query)
            kind = (qs.get("kind", ["ip"])[0] or "ip").lower()
            try:
                lim = min(int(qs.get("limit", ["10"])[0]), 200)
            except Exception:
                lim = 10
            resp = json.dumps(ambil_statistik(kind, lim), ensure_ascii=False)
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(resp.encode())
            return

        if self.path.startswith("/cf_events.json"):
            from urllib.parse import urlparse, parse_qs
            qs = parse_qs(urlparse(self.path).query)
            try:
                lim = min(int(qs.get("limit", ["100"])[0]), 500)
            except Exception:
                lim = 100
            resp = json.dumps(ambil_event(lim), ensure_ascii=False)
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(resp.encode())
            return

        if self.path == "/metrics.json":
            # Array format that Infinity auto-detects
            data = []
            metrics = SINGLE
            for name in metrics:
                results = cache.get(name, [])
                val = results[0].get("value", 0) if results else 0
                try:
                    data.append({"metric": name, "value": int(val)})
                except Exception:
                    data.append({"metric": name, "value": 0})

            for r in cache.get("vl_logs_by_host", []):
                host = r.get("host", "unknown")
                val = r.get("value", 0)
                try:
                    data.append({"metric": "vl_logs_by_host", "vm_host": host, "value": int(val)})
                except Exception:
                    pass

            resp = json.dumps(data)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(resp.encode())
            return

        lines = ["# HELP vl_logs_total Total log entries (last 5m)", "# TYPE vl_logs_total gauge"]

        # Single value metrics
        for name in SINGLE:
            results = cache.get(name, [])
            val = results[0].get("value", 0) if results else 0
            try:
                val = int(val)
            except Exception:
                val = 0
            lines.append(f"{name} {val}")

        # By-host metrics
        if cache.get("vl_logs_by_host"):
            lines.append("")
            lines.append("# HELP vl_logs_by_host Log entries by host (last 5m)")
            lines.append("# TYPE vl_logs_by_host gauge")
            for r in cache.get("vl_logs_by_host", []):
                host = r.get("host", "unknown")
                val = r.get("value", 0)
                try:
                    val = int(val)
                except Exception:
                    val = 0
                lines.append(f'vl_logs_by_host{{vm_host="{host}"}} {val}')

        lines.append(f"# VL exporter scrape time {now}")
        resp = "\n".join(lines) + "\n"

        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(resp.encode())


HTTPServer(("0.0.0.0", 9101), Handler).serve_forever()
