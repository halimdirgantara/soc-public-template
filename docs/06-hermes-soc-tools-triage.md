# Hermes Agent and SOC Tools Triage

> Public-safe implementation note for `soc-public-template`.
>
> This document uses sanitized placeholder values throughout. Replace `LOKI_SERVER_IP`, `GRAFANA_SERVER_IP`, `HERMES_NODE_IP`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, and any instance-specific labels before using in production.

## 1. Purpose

Hermes is used as a SOC assistant to help operators perform:

- Grafana/Loki alert triage
- Laravel log analysis
- SSH brute-force investigation
- Fail2Ban, UFW, and Promtail status checks
- Incident summary drafting
- Containment recommendations that always wait for operator approval

Hermes should not be granted automatic rights to delete files, block IPs, stop services, or modify firewall rules without explicit operator confirmation.

## 2. Reference Architecture

```text
Application Servers / VM
        |
    Promtail
        v
   Loki Server
        v
 Grafana Alerting
        |
  Telegram / Webhook / Operator Prompt
        v
  Hermes Agent / Gateway
        v
    SOC Operator
```

Example environment variables (sanitized):

```bash
SOC_LOKI_URL="http://LOKI_SERVER_IP:3100"
SOC_GRAFANA_URL="http://GRAFANA_SERVER_IP"
SOC_INSTANSI="example-org"
```

For public repositories, use placeholders such as `LOKI_SERVER_IP`, `GRAFANA_SERVER_IP`, `HERMES_NODE_IP`, `TELEGRAM_BOT_TOKEN`, and `TELEGRAM_CHAT_ID`.

## 3. Hermes Server Prerequisites

Recommended minimum:

```text
OS      : Ubuntu 22.04 / 24.04 or Debian 12
CPU     : 2 vCPU
RAM     : 4 GB
Disk    : 40 GB+
Network : access to Loki, Grafana, and internet for Telegram/API
User    : non-root user with sudo
```

Install base packages:

```bash
sudo apt update
sudo apt install -y \
  curl wget git jq unzip tar rsync \
  python3 python3-venv python3-pip \
  ripgrep net-tools lsof \
  ca-certificates gnupg
```

Validate:

```bash
python3 --version
git --version
jq --version
rg --version
```

## 4. Installing Hermes Agent

Run the Hermes installer using the official method for your organisation. After installation, the expected structure is:

```text
~/.hermes/
~/.hermes/config.yaml
~/.hermes/.env
~/.hermes/hermes-agent/
~/.local/bin/hermes
```

Validate:

```bash
which hermes || ls -lah ~/.local/bin/hermes
hermes doctor
```

If `hermes` is not in PATH:

```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

## 5. API Key and Telegram Configuration

Edit the Hermes environment file:

```bash
nano ~/.hermes/.env
```

Example contents (replace all placeholder values):

```bash
TELEGRAM_BOT_TOKEN="TELEGRAM_BOT_TOKEN"
TELEGRAM_ALLOWED_USERS="TELEGRAM_CHAT_ID"
TELEGRAM_HOME_CHANNEL="TELEGRAM_CHAT_ID"
OPENROUTER_API_KEY="YOUR_OPENROUTER_API_KEY"
SOC_LOKI_URL="http://LOKI_SERVER_IP:3100"
SOC_GRAFANA_URL="http://GRAFANA_SERVER_IP"
SOC_INSTANSI="example-org"
```

Secure permissions:

```bash
chmod 600 ~/.hermes/.env
```

Test Telegram without exposing the token in shell history:

```bash
set -a
source ~/.hermes/.env
set +a
curl -s "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getMe" | jq
curl -s "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
  -d "chat_id=${TELEGRAM_HOME_CHANNEL}" \
  -d "text=Test Hermes Gateway from SOC node" | jq
```

If `sendMessage` returns `chat not found`, the operator account must first send a message to the bot.

## 6. Running Hermes Gateway as a User Service

Enable linger so the systemd user service persists after logout:

```bash
sudo loginctl enable-linger "$USER"
loginctl show-user "$USER" | grep -i linger
```

Validate the service:

```bash
systemctl --user status hermes-gateway --no-pager
systemctl --user is-enabled hermes-gateway
systemctl --user is-active hermes-gateway
```

If the service is not yet active:

```bash
systemctl --user daemon-reload
systemctl --user enable --now hermes-gateway
```

Check logs:

```bash
journalctl --user -u hermes-gateway -n 100 --no-pager
```

## 7. Validating Loki and Grafana Connectivity

From the Hermes node:

```bash
set -a
source ~/.hermes/.env
set +a
curl -s "$SOC_LOKI_URL/ready"
curl -s "$SOC_LOKI_URL/loki/api/v1/labels" | jq
curl -s "$SOC_LOKI_URL/loki/api/v1/label/host/values" | jq
```

Expected Loki response:

```text
ready
```

## 8. Creating Local SOC Tools

Create the tools folder:

```bash
mkdir -p ~/soc-tools
```

Scripts live in this repo under `scripts/soc-tools/`. Copy and adapt them to `~/soc-tools/` on the Hermes node — see section 15 for the recommended repo layout.

### 8.1 Laravel Error Triage

See `scripts/soc-tools/loki-triage.example.sh`.

Usage:

```bash
~/soc-tools/loki-triage.sh "web-admin" ".*" "30m"
```

### 8.2 SSH Brute-Force Triage

See `scripts/soc-tools/ssh-triage.example.sh`.

Usage:

```bash
~/soc-tools/ssh-triage.sh "web-admin" "30m"
```

### 8.3 Malware Watch Summary

If the server has `server-malware-watch-v2` installed, see `scripts/soc-tools/malware-watch-summary.example.sh`.

Usage:

```bash
~/soc-tools/malware-watch-summary.sh "web-opd-filament"
```

## 9. Adding a Local SOC Skill to Hermes

Create the skill folder:

```bash
mkdir -p ~/.hermes/skills/soc-local
nano ~/.hermes/skills/soc-local/SKILL.md
```

Use the template from `skills/08-hermes-soc-local/SKILL.md` in this repository. Replace `example-org` with your instance label before deploying to production.

Restart Hermes Gateway:

```bash
systemctl --user restart hermes-gateway
journalctl --user -u hermes-gateway -n 80 --no-pager
```

Validate:

```bash
hermes doctor
hermes skills list
```

If `hermes skills list` is unavailable:

```bash
hermes skills --help
```

## 10. Adding Public Cybersecurity Skills

Clone the skills repository:

```bash
mkdir -p ~/hermes-skill-sources
cd ~/hermes-skill-sources
git clone https://github.com/mukul975/Anthropic-Cybersecurity-Skills.git
cd Anthropic-Cybersecurity-Skills
```

Inspect the structure:

```bash
ls -lah
find skills -maxdepth 2 -type f -name "SKILL.md" | head -50
find skills -maxdepth 2 -type f -name "SKILL.md" | wc -l
```

For production SOC, import a defensive subset first rather than all skills at once:

```bash
mkdir -p ~/.hermes/skills/cybersecurity-defensive

for s in \
  detecting-cryptomining-in-cloud \
  hunting-for-unusual-service-installations \
  configuring-host-based-intrusion-detection \
  detecting-anomalous-authentication-patterns \
  hunting-for-dns-based-persistence \
  building-incident-response-playbook \
  implementing-ransomware-kill-switch-detection \
  detecting-kerberoasting-attacks \
  detecting-process-injection-techniques \
  conducting-malware-incident-response \
  building-vulnerability-dashboard-with-defectdojo \
  testing-api-authentication-weaknesses
do
  if [ -d "skills/$s" ]; then
    rsync -av "skills/$s/" "$HOME/.hermes/skills/cybersecurity-defensive/$s/"
  fi
done

chmod -R u+rwX,go-rwx ~/.hermes/skills/cybersecurity-defensive
```

Restart Hermes:

```bash
systemctl --user restart hermes-gateway
hermes doctor
```

## 11. SOUL.md Guardrail Policy

Add SOC operational policy to `~/.hermes/SOUL.md`:

```bash
nano ~/.hermes/SOUL.md
```

Append:

```markdown
## SOC Cybersecurity Skill Policy

When using cybersecurity skills:

1. Prioritise defensive use: detection, triage, incident response, hardening, and evidence preservation.
2. Do not perform offensive actions, credential attacks, exploitation, C2 setup, persistence, or destructive steps unless explicitly authorised in a lab or penetration test context.
3. For production SOC systems, never run commands that delete, stop, block, ban, quarantine, or modify firewall rules without explicit operator confirmation.
4. Use Loki, Grafana, Fail2Ban, Promtail, UFW, and system logs as evidence sources.
5. In operator-facing responses, separate evidence from assumptions.
6. For malware incidents, preserve evidence before containment.
7. For firewall or Fail2Ban actions, show the proposed command and expected impact before execution.
```

Restart:

```bash
systemctl --user restart hermes-gateway
```

## 12. Hermes Triage Prompt Examples

SSH brute-force:

```text
Use the SOC local skill and local tools. Triage SSH brute-force for host web-admin over the last 30 minutes.
Do not run destructive commands. Show evidence from Loki, a true/false positive conclusion, and a safe recommendation.
```

Laravel error:

```text
Use the SOC local skill. Investigate Laravel production.ERROR on app web-opd-filament over the last 1 hour.
Pull data from Loki, show sample log lines, host, app, event count, and likely cause. Do not modify the system.
```

Malware watch:

```text
Use the SOC local skill. Run malware watch summary for app web-opd-filament.
Separate critical, warning, and containment recommendations. Do not quarantine before I approve.
```

Grafana alert:

```text
I have a Grafana alert. Triage it with the SOC workflow: validate in Loki, check host/app, count events,
find sample logs, draw a conclusion, then recommend non-destructive actions.
```

## 13. Grafana Alert Integration

Recommended safe mode:

```text
Grafana Alert
     ↓
Telegram / Webhook
     ↓
Hermes creates triage
     ↓
Operator reviews
     ↓
Operator approves action
```

Do not use automated mode:

```text
Grafana Alert → Hermes → auto delete file / block IP / kill process
```

In production, all of the following must require explicit operator approval:

- `ufw deny`
- `fail2ban-client set ... banip`
- `rm`
- `mv` to quarantine
- `pkill`
- `systemctl stop`
- Changes to Nginx or PHP-FPM configuration

## 14. Daily Operational Commands

Check Hermes Gateway:

```bash
systemctl --user status hermes-gateway --no-pager
journalctl --user -u hermes-gateway -n 80 --no-pager
```

Check Loki:

```bash
curl -s "$SOC_LOKI_URL/ready"
curl -s "$SOC_LOKI_URL/loki/api/v1/labels" | jq
```

Check malware watch:

```bash
sudo /usr/local/sbin/server-malware-watch-v2 --app web-opd-filament || true
```

Check malware watch timer:

```bash
systemctl status malware-watch.timer --no-pager
journalctl -u malware-watch -n 80 --no-pager
```

Check SSH attacks:

```bash
~/soc-tools/ssh-triage.sh ".*" "30m"
```

Check Laravel errors:

```bash
~/soc-tools/loki-triage.sh ".*" ".*" "30m"
```

## 15. Recommended Repository Structure

```text
soc-public-template/
├── docs/
│   └── 06-hermes-soc-tools-triage.md   ← this document
├── scripts/
│   └── soc-tools/
│       ├── loki-triage.example.sh
│       ├── ssh-triage.example.sh
│       └── malware-watch-summary.example.sh
└── skills/
    └── 08-hermes-soc-local/
        └── SKILL.md
```

## 16. Troubleshooting

### Hermes not reading `.env`

```bash
ls -lah ~/.hermes/.env
chmod 600 ~/.hermes/.env
systemctl --user restart hermes-gateway
```

### Telegram `Chat not found`

```bash
curl -s "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getUpdates" | jq
```

Send at least one message from the operator account to the bot first, then retry.

### Loki unreachable

```bash
curl -v "$SOC_LOKI_URL/ready"
ip route
ss -tupna | grep 3100
```

### Hermes Gateway stops after logout

```bash
sudo loginctl enable-linger "$USER"
loginctl show-user "$USER" | grep -i linger
systemctl --user restart hermes-gateway
```

### Skills not appearing

```bash
find ~/.hermes/skills -maxdepth 3 -name SKILL.md -ls
hermes doctor
systemctl --user restart hermes-gateway
```

## 17. Security Notes

- Hermes is an assistant, not a full SIEM/SOAR replacement.
- Use Hermes to accelerate analysis, not for auto-remediation without control.
- All destructive commands must request operator approval.
- All malware containment must preserve evidence and file hashes first.
- Only push sanitised templates to the public repository.
- Never commit tokens, API keys, real IP addresses, or production credentials.
