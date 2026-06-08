# Skill: CrowdSec and Bouncer Public Template

## Purpose

Use this skill for public-safe CrowdSec acquisition and firewall bouncer examples.

## Rules

- Do not include production LAPI URLs.
- Do not commit bouncer keys.
- Use dummy decision IP `1.2.3.4` only for test examples.
- Include whitelist warning before bouncer activation.

## Validation

```bash
sudo cscli metrics
sudo cscli decisions list
sudo cscli bouncers list
```
