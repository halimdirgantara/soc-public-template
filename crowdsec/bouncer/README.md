# CrowdSec Firewall Bouncer

This folder contains public-safe notes and placeholders for CrowdSec Firewall Bouncer.

Do not commit:

- Bouncer API keys
- `local_api_credentials.yaml`
- Real production LAPI URLs if sensitive
- Real private IP topology

## Validation

```bash
sudo systemctl status crowdsec-firewall-bouncer --no-pager
sudo cscli bouncers list
sudo cscli decisions list
sudo iptables -L CROWDSEC_CHAIN -n -v
sudo ipset list | grep -A 20 -i crowdsec
```

## Dummy Test

```bash
sudo cscli decisions add --ip 1.2.3.4 --duration 5m --reason "manual firewall bouncer test"
sudo cscli decisions list
sudo cscli decisions delete --ip 1.2.3.4
```