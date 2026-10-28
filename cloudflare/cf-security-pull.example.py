#!/usr/bin/env python3
"""Tarik Security Events Cloudflare -> VictoriaLogs.

Dipakai oleh cron 5 menit di VM SOC. Read-only terhadap Cloudflare.

Sumber: GraphQL firewallEventsAdaptive (retensi 30 hari pada paket Pro).
Tujuan: VictoriaLogs stream  job=cf-security,zone=<zona>

Konfigurasi (environment):
  CF_API_TOKEN_FILE  default ~/.cf-soc/token   (isi: account_id|token, mode 600)
  VL_URL             default http://10.0.0.30:9428
  CF_LOOKBACK_MIN    default 15 (menit)
"""
import json, os, sqlite3, sys, time, datetime, urllib.request, urllib.error

ZONE = os.environ.get("CF_ZONE_ID", "")
ZONE_NAME = os.environ.get("CF_ZONE_NAME", "example.go.id")
HOME = os.path.expanduser("~")
TOKEN_FILE = os.environ.get("CF_API_TOKEN_FILE", f"{HOME}/.cf-soc/token")
STATE_DB = os.environ.get("CF_STATE_DB", f"{HOME}/.cf-soc/seen.db")
VL_URL = os.environ.get("VL_URL", "http://10.0.0.30:9428").rstrip("/")
LOOKBACK = int(os.environ.get("CF_LOOKBACK_MIN", "15"))
BACKFILL_H = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[1] == "--hours" else 0

QUERY = """
query($zone: String!, $since: Time!, $limit: Int!) {
  viewer {
    zones(filter: {zoneTag: $zone}) {
      firewallEventsAdaptive(limit: $limit, filter: {datetime_gt: $since},
                             orderBy: [datetime_ASC]) {
        datetime action clientIP clientCountryName clientAsn
        clientRequestHTTPMethodName clientRequestPath clientRequestQuery
        edgeResponseStatus userAgent ruleId description rayName clientRequestHTTPHost
      }
    }
  }
}
"""


def load_token():
    with open(TOKEN_FILE) as f:
        acc, tok = [x.strip() for x in f.read().strip().split("|")]
    return acc, tok


def graphql(tok, since, limit=5000, max_pages=40):
    """Ambil event sejak `since`, dipaginasi per 5000 baris."""
    semua, cursor = [], since
    for _ in range(max_pages):
        body = json.dumps({"query": QUERY,
                           "variables": {"zone": ZONE, "since": cursor, "limit": limit}}).encode()
        req = urllib.request.Request("https://api.cloudflare.com/client/v4/graphql", data=body,
                                     headers={"Authorization": f"Bearer {tok}",
                                              "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=120) as r:
            d = json.load(r)
        if d.get("errors"):
            raise RuntimeError(json.dumps(d["errors"])[:400])
        batch = d["data"]["viewer"]["zones"][0]["firewallEventsAdaptive"]
        if not batch:
            break
        semua += batch
        if len(batch) < limit:
            break
        baru_cursor = max(x["datetime"] for x in batch)
        if baru_cursor <= cursor:
            break
        cursor = baru_cursor
    return semua


def db():
    os.makedirs(os.path.dirname(STATE_DB), exist_ok=True)
    c = sqlite3.connect(STATE_DB)
    c.execute("CREATE TABLE IF NOT EXISTS seen(ray TEXT, action TEXT, ts TEXT, PRIMARY KEY(ray, action))")
    c.execute("DELETE FROM seen WHERE ts < datetime('now','-7 day')")
    return c


def main():
    acc, tok = load_token()
    conn = db()

    if BACKFILL_H:
        since = (datetime.datetime.utcnow() - datetime.timedelta(hours=BACKFILL_H)).strftime("%Y-%m-%dT%H:%M:%SZ")
    else:
        row = conn.execute("SELECT MAX(ts) FROM seen").fetchone()
        if row and row[0]:
            since = row[0]
        else:
            since = (datetime.datetime.utcnow() - datetime.timedelta(minutes=LOOKBACK)).strftime("%Y-%m-%dT%H:%M:%SZ")

    events = graphql(tok, since)
    baru, lines = 0, []
    for e in events:
        ray = e.get("rayName") or ""
        act = e.get("action") or ""
        key = (ray, act)
        if ray and conn.execute("SELECT 1 FROM seen WHERE ray=? AND action=?", key).fetchone():
            continue
        ts = e.get("datetime", "")
        msg = (f"{act} {e.get('clientIP')} {e.get('clientRequestHTTPMethodName','')} "
               f"{e.get('clientRequestHTTPHost','')}{e.get('clientRequestPath','')} "
               f"[{e.get('description') or e.get('ruleId') or '-'}]")
        rec = {
            "_time": ts,
            "_msg": msg,
            "job": "cf-security",
            "zone": ZONE_NAME,
            "action": act,
            "ip": e.get("clientIP"),
            "country": e.get("clientCountryName"),
            "asn": e.get("clientAsn"),
            "method": e.get("clientRequestHTTPMethodName"),
            "host": e.get("clientRequestHTTPHost"),
            "path": e.get("clientRequestPath"),
            "query": e.get("clientRequestQuery"),
            "status": e.get("edgeResponseStatus"),
            "ua": e.get("userAgent"),
            "rule_id": e.get("ruleId"),
            "rule_name": e.get("description"),
            "ray": ray,
        }
        lines.append(json.dumps(rec, ensure_ascii=False))
        if ray:
            conn.execute("INSERT OR REPLACE INTO seen VALUES(?,?,?)", (ray, act, ts))
        baru += 1
    conn.commit()

    if lines:
        data = ("\n".join(lines)).encode()
        url = f"{VL_URL}/insert/jsonline?_stream_fields=job,zone"
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/stream+json"})
        with urllib.request.urlopen(req, timeout=60) as r:
            r.read()

    print(f"{datetime.datetime.utcnow().isoformat(timespec='seconds')}Z since={since} "
          f"event={len(events)} baru={baru} terkirim={len(lines)}")


if __name__ == "__main__":
    main()
