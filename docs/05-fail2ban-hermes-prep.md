# Fail2Ban Hardening and Hermes Agent Preparation

> Public-safe implementation note for `soc-public-template`.
>
> This document intentionally uses sanitized example IPs, hostnames, users, and labels. Do not commit production IP addresses, public hostnames, SSH keys, passwords, tokens, Telegram credentials, Cloudflare credentials, or real inventory values to a public repository.

## 1. Purpose

This document describes a repeatable implementation workflow for preparing Linux virtual machines before installing a Hermes Agent or similar security notification agent.

The preparation focuses on:

- SSH key-based access.
- Non-interactive sudo readiness for automation.
- Fail2Ban installation and SSH jail activation.
- Promtail service validation.
- UFW baseline firewall activation.
- Handling special hosts that use a different SSH user.
- Troubleshooting apt lock, sudo password issues, and SSH permission errors.

This procedure is designed for a lightweight SOC deployment using Grafana, Loki, Promtail, Fail2Ban, UFW, Telegram alerting, and optional Hermes-style notification integration.

## 2. Public Repository Safety Rules

This file is intended for a public template repository. Keep the following values sanitized:

| Sensitive item | Use in public repo |
|---|---|
| Production private IP | Use `10.0.0.x` or `192.0.2.x` examples |
| Production public IP | Use `203.0.113.x` examples |
| Real hostname/domain | Use `host-example.local` or `server.example.org` |
| SSH private key | Never commit |
| SSH public key tied to production | Avoid committing unless it is a dummy example |
| Telegram bot token | Never commit |
| Cloudflare tunnel token | Never commit |
| Real VM inventory | Keep in private repo |
| Passwords and sudo credentials | Never commit |

Recommended repository split:

- Public repo: generic scripts, sanitized examples, documentation, templates.
- Private repo: production inventory, real hostnames, real IP addresses, actual deployment status, secrets references.

## 3. Example Final Target State

Each managed VM should reach this state before Hermes Agent deployment:

```text
SSH       = OK
SUDO      = OK
FAIL2BAN  = active
SSHD jail = active
PROMTAIL  = active
UFW       = active
APT       = OK
```

Example sanitized final check output:

```text
IP=10.0.0.26
HOST=host-example.local
USER=appuser
SUDO=OK
FAIL2BAN=active
PROMTAIL=active
UFW=Status: active
Status for the jail: sshd
|- Filter
|  |- Currently failed: 0
|  |- Total failed:     0
|  `- File list:        /var/log/auth.log
`- Actions
   |- Currently banned: 0
   |- Total banned:     0
   `- Banned IP list:
```

## 4. Operator Prompt for Implementation

Use this prompt when asking an operator or AI assistant to continue the deployment workflow:

```text
Act as a DevOps/SOC engineer. Continue hardening a Linux VM fleet before Hermes Agent installation.

Current goals:
1. Validate SSH key login.
2. Validate non-interactive sudo.
3. Install and enable Fail2Ban.
4. Configure Fail2Ban sshd jail.
5. Validate Promtail.
6. Enable UFW safely without locking out SSH.
7. Record special hosts that require a non-default SSH user.
8. Produce a final readiness status for Hermes Agent deployment.

Constraints:
- Do not expose real IP addresses, real hostnames, tokens, or SSH private keys in public documentation.
- Do not run destructive commands without checking the active process first.
- Do not enable UFW before allowing SSH from trusted admin networks.
- Prefer non-interactive sudo for automation, but configure it explicitly and safely.

Expected output:
- Exact shell commands.
- Validation commands.
- Troubleshooting branch for apt lock, permission denied, sudo password required, and inactive services.
- Final readiness checklist.
```

## 5. Inventory Format

Use a public-safe example inventory for documentation:

```csv
ip,ssh_user,host,role,notes
10.0.0.10,linux,app-01,web,standard-user
10.0.0.11,linux,db-01,database,standard-user
10.0.0.26,appuser,domain-01,dns-or-domain,special-ssh-user
```

For private production use, keep the real inventory in a private repository or an untracked local file. Note: this is a slim inventory schema for the readiness workflow only — the canonical fleet inventory format used elsewhere in this repo is `inventory/hosts.example.csv`.

Suggested `.gitignore` entries:

```gitignore
inventory/*.private.csv
inventory/*production*.csv
*.pem
*.key
.env
.env.*
```

## 6. SSH Key Access for a Special Host

A special host may use a non-default SSH account, for example `appuser` instead of `linux`.

From the control machine, confirm the public key:

```bash
cat ~/.ssh/id_rsa.pub
```

If an RSA key does not exist:

```bash
ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa -C "soc-autoscan"
cat ~/.ssh/id_rsa.pub
```

On the target VM, via console or an existing administrative login:

```bash
sudo mkdir -p /home/appuser/.ssh
sudo nano /home/appuser/.ssh/authorized_keys
sudo chown -R appuser:appuser /home/appuser/.ssh
sudo chmod 700 /home/appuser/.ssh
sudo chmod 600 /home/appuser/.ssh/authorized_keys
```

Validate from the control machine:

```bash
ssh -i ~/.ssh/id_rsa appuser@10.0.0.26 "hostname && whoami"
```

Expected output:

```text
host-example.local
appuser
```

If `Host key verification failed` appears:

```bash
ssh-keygen -R 10.0.0.26
ssh -i ~/.ssh/id_rsa appuser@10.0.0.26
```

Accept the host key only after confirming it is the expected server.

## 7. Validate Non-Interactive Sudo

From the control machine:

```bash
ssh -i ~/.ssh/id_rsa appuser@10.0.0.26 "sudo -n true && echo SUDO_OK || echo SUDO_NEED_PASSWORD"
```

Expected:

```text
SUDO_OK
```

If the output is `SUDO_NEED_PASSWORD`, configure a sudoers rule from console/root or another admin account:

```bash
echo 'appuser ALL=(ALL) NOPASSWD:ALL' | sudo tee /etc/sudoers.d/appuser-autoscan
sudo chmod 440 /etc/sudoers.d/appuser-autoscan
sudo visudo -cf /etc/sudoers.d/appuser-autoscan
```

Validate again:

```bash
ssh -i ~/.ssh/id_rsa appuser@10.0.0.26 "sudo -n true && echo SUDO_OK || echo SUDO_NEED_PASSWORD"
```

Security note: `NOPASSWD:ALL` is operationally convenient but broad. For stricter environments, restrict allowed commands to only the specific systemctl, apt, install, and configuration commands required by the deployment process.

## 8. Install and Enable Fail2Ban

From the control machine:

```bash
ssh -i ~/.ssh/id_rsa appuser@10.0.0.26 "sudo apt update && sudo apt install -y fail2ban && sudo systemctl enable --now fail2ban"
```

Validate:

```bash
ssh -i ~/.ssh/id_rsa appuser@10.0.0.26 "sudo systemctl is-active fail2ban"
```

Expected:

```text
active
```

## 9. Configure Fail2Ban SSH Jail

Install the standard sshd jail configuration:

```bash
ssh -i ~/.ssh/id_rsa appuser@10.0.0.26 'sudo mkdir -p /etc/fail2ban/jail.d && sudo tee /etc/fail2ban/jail.d/sshd-soc.local > /dev/null <<"REMOTE_EOF"
[sshd]
enabled = true
port = ssh
filter = sshd
backend = systemd
logpath = /var/log/auth.log
maxretry = 5
findtime = 10m
bantime = 1h
ignoreip = 127.0.0.1/8 10.0.0.0/24 172.16.0.0/12
REMOTE_EOF

sudo fail2ban-client -t
sudo systemctl restart fail2ban
sudo fail2ban-client status sshd'
```

Expected status:

```text
Status for the jail: sshd
```

Notes:

- `ignoreip` should include loopback and trusted admin networks.
- Replace `10.0.0.0/24` and `172.16.0.0/12` with private inventory values in the private repository only.
- Do not whitelist unknown public networks.

## 10. Validate Promtail

```bash
ssh -i ~/.ssh/id_rsa appuser@10.0.0.26 "sudo systemctl is-active promtail || true"
```

Expected:

```text
active
```

If missing or inactive, deploy Promtail using the repository's Promtail agent script or your internal deployment script. Keep real Loki URLs and labels in the private repository.

## 11. Enable UFW Safely

Do not enable UFW before allowing SSH from trusted admin networks.

Example baseline:

```bash
ssh -i ~/.ssh/id_rsa appuser@10.0.0.26 "
sudo ufw --force reset
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow from 10.0.0.0/24 to any port 22 proto tcp comment 'Allow SSH trusted internal network'
sudo ufw allow from 172.16.0.0/12 to any port 22 proto tcp comment 'Allow SSH VPN/internal network'
sudo ufw --force enable
sudo ufw status verbose
"
```

If the host serves public HTTP/HTTPS traffic:

```bash
ssh -i ~/.ssh/id_rsa appuser@10.0.0.26 "
sudo ufw allow 80/tcp comment 'HTTP'
sudo ufw allow 443/tcp comment 'HTTPS'
sudo ufw status numbered
"
```

Validate:

```bash
ssh -i ~/.ssh/id_rsa appuser@10.0.0.26 "sudo ufw status | head -n1"
```

Expected:

```text
Status: active
```

## 12. Final Readiness Check

Run this from the control machine:

```bash
ssh -i ~/.ssh/id_rsa appuser@10.0.0.26 "
echo IP=10.0.0.26
echo HOST=\$(hostname)
echo USER=\$(whoami)
echo SUDO=\$(sudo -n true && echo OK || echo BAD)
echo FAIL2BAN=\$(systemctl is-active fail2ban)
echo PROMTAIL=\$(systemctl is-active promtail 2>/dev/null || echo missing)
echo UFW=\$(sudo ufw status | head -n1)
sudo fail2ban-client status sshd
"
```

Target result:

```text
SUDO=OK
FAIL2BAN=active
PROMTAIL=active
UFW=Status: active
Status for the jail: sshd
```

## 13. Troubleshooting

### 13.1 SSH Permission Denied

Symptoms:

```text
Permission denied (publickey)
Permission denied (password)
```

Checks:

```bash
ssh -vvv -i ~/.ssh/id_rsa appuser@10.0.0.26
```

On target:

```bash
id appuser
getent passwd appuser
ls -ld /home/appuser /home/appuser/.ssh
ls -l /home/appuser/.ssh/authorized_keys
```

Expected permissions:

```text
drwx------ appuser appuser /home/appuser/.ssh
-rw------- appuser appuser /home/appuser/.ssh/authorized_keys
```

### 13.2 Invalid User During chown

Symptom:

```text
chown: invalid user: 'linux:linux'
```

Cause: the target VM does not have a `linux` user.

Fix: use the actual target user:

```bash
sudo chown -R appuser:appuser /home/appuser/.ssh
```

### 13.3 Sudo Requires Password

Symptom:

```text
sudo: a password is required
SUDO_NEED_PASSWORD
```

Fix from console/root:

```bash
echo 'appuser ALL=(ALL) NOPASSWD:ALL' | sudo tee /etc/sudoers.d/appuser-autoscan
sudo chmod 440 /etc/sudoers.d/appuser-autoscan
sudo visudo -cf /etc/sudoers.d/appuser-autoscan
```

### 13.4 Apt Lock

Symptom:

```text
Could not get lock /var/lib/dpkg/lock-frontend. It is held by process <PID> (apt-get)
```

Do not delete the lock first. Inspect the process:

```bash
ps -fp <PID>
pstree -ap <PID>
ps aux | grep -E "apt|dpkg|unattended|packagekit" | grep -v grep
```

If the process is active, wait. To observe apt logs:

```bash
sudo tail -f /var/log/apt/term.log
```

If the process is confirmed stuck:

```bash
sudo kill -TERM <PID>
sleep 10
ps -p <PID>
```

If still running:

```bash
sudo kill -KILL <PID>
```

Repair dpkg:

```bash
sudo dpkg --configure -a
sudo apt -f install
sudo apt update
```

Only remove stale locks after confirming no apt/dpkg process remains:

```bash
sudo rm -f /var/lib/dpkg/lock-frontend
sudo rm -f /var/lib/dpkg/lock
sudo rm -f /var/cache/apt/archives/lock
sudo dpkg --configure -a
sudo apt update
```

### 13.5 Fail2Ban Inactive

```bash
sudo systemctl status fail2ban --no-pager
sudo journalctl -u fail2ban -n 100 --no-pager
sudo fail2ban-client -t
```

Common fixes:

```bash
sudo apt install -y fail2ban
sudo systemctl enable --now fail2ban
sudo systemctl restart fail2ban
```

### 13.6 UFW Inactive

Check current rules:

```bash
sudo ufw status verbose
```

Safely activate:

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow from 10.0.0.0/24 to any port 22 proto tcp
sudo ufw --force enable
```

### 13.7 No Route to Host

Symptoms:

```text
No route to host
Connection timed out
```

Checks from the control machine:

```bash
ping -c 3 10.0.0.21
nc -vz 10.0.0.21 22
ip route get 10.0.0.21
```

Likely causes:

- VM powered off.
- Wrong VLAN.
- Routing issue.
- Firewall between control machine and VM.
- SSH service down.

This issue cannot be fixed by Fail2Ban. Resolve network reachability first.

## 14. Repo Placement

This document lives at:

```text
docs/05-fail2ban-hermes-prep.md
```

Supporting files in this repo:

```text
inventory/hosts.example.csv
scripts/validate-host-readiness.example.sh
```

## 15. Validation Script

A reference validation stub lives at `scripts/validate-host-readiness.example.sh`. It is a sanitized template — copy it into your private repo and adapt as needed.

Usage:

```bash
chmod +x scripts/validate-host-readiness.example.sh
./scripts/validate-host-readiness.example.sh appuser@10.0.0.26
```
