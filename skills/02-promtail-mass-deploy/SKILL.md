# Skill: Promtail Public Template

## Purpose

Use this skill when editing Promtail templates or mass deployment examples.

## Rules

- Use dummy inventory.
- Do not hardcode real SSH users beyond generic examples.
- Do not include passwords.
- Use `ssh -n` in loop examples to prevent SSH from consuming STDIN.
- Keep custom log paths generic.

## Validation

```bash
sudo systemctl status promtail --no-pager
sudo journalctl -u promtail --since "30 minutes ago" --no-pager
```