#!/usr/bin/env python3
"""Auto-ban IP penyerang di Cloudflare berdasarkan volume serangan.

Aturan: IP dengan >= THRESHOLD blokir dalam WINDOW menit terakhir dimasukkan
ke custom rule "SOC - Auto-ban (otomatis)" selama DURATION jam.

Sumber data : VictoriaLogs, stream job=cf-security (pipeline cf_security_pull.py)
Aksi        : menulis satu custom rule WAF (bukan rate limiting) — tanpa kuota 2 rule

Contoh:
  cf_autoban.py --dry-run
  cf_autoban.py --threshold 50 --window 15 --hours 24
"""
import argparse, ipaddress, json, os, sqlite3, sys, time, urllib.parse, urllib.request

CF_API = "https://api.cloudflare.com/client/v4"
ZONE = os.environ.get("CF_ZONE_ID", "")
VL_URL = os.environ.get("VL_URL", "http://10.0.0.30:9428").rstrip("/")
HOME = os.path.expanduser("~")
TOKEN_FILE = os.environ.get("CF_API_TOKEN_FILE", f"{HOME}/.cf-soc/token")
STATE = os.environ.get("CF_AUTOBAN_STATE", f"{HOME}/.cf-soc/bans.json")
ALLOW_FILE = os.environ.get("CF_AUTOBAN_ALLOW", f"{HOME}/.cf-soc/allow.txt")
RULE_DESC = os.environ.get("CF_AUTOBAN_RULE", "SOC - Auto-ban (otomatis)")
PLACEHOLDER = "192.0.2.1"  # TEST-NET, tidak pernah dipakai
MAX_IPS = 150
BOT_FILE = os.environ.get("SOC_BOT_TOKEN_FILE", f"{HOME}/.soc-bot/token")


def kirim_bot(teks):
    """Kirim notifikasi ke bot SOC (format file: token|chat_id)."""
    try:
        with open(BOT_FILE) as f:
            tok, chat = f.read().strip().split("|")
        data = json.dumps({"chat_id": chat, "text": teks, "parse_mode": "HTML",
                           "disable_web_page_preview": True}).encode()
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{tok}/sendMessage",
            data=data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r).get("ok", False)
    except Exception as e:
        print(f"  ! gagal kirim bot: {type(e).__name__}", file=sys.stderr)
        return False


def token():
    with open(TOKEN_FILE) as f:
        return f.read().strip().split("|")[1]


def cf(path, method="GET", body=None, tok=None):
    url = CF_API + path
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method,
                                 headers={"Authorization": f"Bearer {tok or token()}",
                                          "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=45) as r:
        return json.load(r)


def vl(sql):
    url = f"{VL_URL}/select/logsql/query?query=" + urllib.parse.quote(sql)
    with urllib.request.urlopen(url, timeout=45) as r:
        return [json.loads(x) for x in r.read().decode().strip().split("\n") if x]


def kandidat(threshold, window):
    rows = vl(f"_time:{window}m job:cf-security action:block | stats by (ip, country) "
              f"count() as serangan | sort by (serangan) desc | limit 300")
    out = []
    for r in rows:
        try:
            n = int(float(r.get("serangan", 0)))
        except Exception:
            continue
        if n >= threshold:
            out.append({"ip": r.get("ip", ""), "negara": r.get("country", ""), "serangan": n})
    return out


def allowlist():
    nets = [ipaddress.ip_network("10.0.0.0/8"), ipaddress.ip_network("172.16.0.0/12"),
            ipaddress.ip_network("192.168.0.0/16"), ipaddress.ip_network("127.0.0.0/8"),
            ipaddress.ip_network("203.0.113.40/32")]
    if os.path.exists(ALLOW_FILE):
        for line in open(ALLOW_FILE):
            line = line.split("#")[0].strip()
            if not line:
                continue
            try:
                nets.append(ipaddress.ip_network(line, strict=False))
            except ValueError:
                pass
    return nets


def diizinkan(ip, nets):
    try:
        a = ipaddress.ip_address(ip)
    except ValueError:
        return True
    return any(a in n for n in nets if n.version == a.version)


def load_state():
    if os.path.exists(STATE):
        try:
            return json.load(open(STATE))
        except Exception:
            pass
    return {}


def save_state(s):
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    tmp = STATE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(s, f, indent=1)
    os.replace(tmp, STATE)


def ruleset_id(tok):
    r = cf(f"/zones/{ZONE}/rulesets/phases/http_request_firewall_custom/entrypoint", tok=tok)
    return r["result"]["id"], r["result"]["rules"]


def terapkan(bans, tok, dry):
    ip_aktif = [ip for ip in bans]
    ekspresi = "ip.src in {" + " ".join(ip_aktif[:MAX_IPS] or [PLACEHOLDER]) + "}"
    rs_id, rules = ruleset_id(tok)
    rules = [r for r in rules if r.get("description") != RULE_DESC]
    rule = {"action": "block", "description": RULE_DESC, "expression": ekspresi,
            "enabled": bool(ip_aktif)}
    pos = next((i for i, r in enumerate(rules)
                if r.get("description", "").startswith("SOC - Allow monitoring checks")), -1)
    baru = rules[:pos + 1] + [rule] + rules[pos + 1:] if pos >= 0 else [rule] + rules
    if dry:
        return ekspresi, len(ip_aktif)
    cf(f"/zones/{ZONE}/rulesets/{rs_id}", "PUT", {"rules": baru}, tok)
    return ekspresi, len(ip_aktif)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--threshold", type=int, default=50)
    ap.add_argument("--window", type=int, default=15, help="menit")
    ap.add_argument("--hours", type=int, default=24, help="durasi ban")
    ap.add_argument("--include-domestic", action="store_true",
                    help="ikutkan IP Indonesia (default: hanya luar negeri)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--quiet", action="store_true", help="cetak hanya bila ada perubahan")
    ap.add_argument("--notify", action="store_true",
                    help="kirim perubahan ban ke bot SOC (Telegram)")
    ap.add_argument("--uji-notif", action="store_true",
                    help="kirim satu pesan uji ke bot SOC lalu keluar")
    a = ap.parse_args()

    if a.uji_notif:
        ok = kirim_bot("🧪 <b>UJI notifikasi auto-ban</b>\n\n"
                       "Mulai sekarang pemberitahuan auto-ban Cloudflare dikirim ke bot ini, "
                       "bukan ke chat pribadi.")
        print("terkirim" if ok else "gagal")
        return

    tok = token()
    now = int(time.time())
    nets = allowlist()
    state = load_state()

    # buang yang kedaluwarsa
    kadaluarsa = [ip for ip, v in state.items() if v.get("sampai", 0) <= now]
    for ip in kadaluarsa:
        del state[ip]

    ditambah = []
    for k in kandidat(a.threshold, a.window):
        ip, negara = k["ip"], k["negara"]
        if not ip or diizinkan(ip, nets):
            continue
        if negara == "ID" and not a.include_domestic:
            continue
        if ip in state:
            state[ip]["serangan"] = max(state[ip].get("serangan", 0), k["serangan"])
            continue
        state[ip] = {"sampai": now + a.hours * 3600, "serangan": k["serangan"],
                     "negara": negara, "dibuat": now}
        ditambah.append(k)

    if not a.dry_run:
        save_state(state)
    ekspresi, jml = terapkan(state, tok, a.dry_run)

    if not a.quiet or ditambah or kadaluarsa:
        print(f"{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(now))} "
              f"kandidat_baru={len(ditambah)} ban_aktif={jml} kedaluwarsa={len(kadaluarsa)}")
    for k in ditambah:
        print(f"  + BAN {k['ip']} ({k['negara']}) {k['serangan']} serangan/15m")
    for ip in kadaluarsa:
        print(f"  - LEPAS {ip} (kedaluwarsa)")
    if jml > MAX_IPS:
        print(f"  ! peringatan: {jml} IP aktif, hanya {MAX_IPS} pertama masuk rule")

    if a.notify and not a.dry_run and (ditambah or kadaluarsa):
        jam = time.strftime("%d %b %Y %H:%M UTC", time.gmtime(now))
        bagian = [f"🚫 <b>Auto-ban Cloudflare</b>\n{jam}"]
        if ditambah:
            bagian.append("<b>Diblokir " + str(a.hours) + " jam</b>\n" + "\n".join(
                f"• {k['ip']} ({k['negara']}) — {k['serangan']} serangan/15 menit"
                for k in ditambah))
        if kadaluarsa:
            bagian.append("<b>Dilepas (kedaluwarsa)</b>\n" +
                          "\n".join(f"• {ip}" for ip in kadaluarsa))
        bagian.append(f"Total ban aktif: <b>{jml}</b>")
        kirim_bot("\n\n".join(bagian))


if __name__ == "__main__":
    main()
