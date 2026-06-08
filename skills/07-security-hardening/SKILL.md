# Skill: Public Repository Security Hardening

## Purpose

Use this skill to protect the public repository from accidental secret or production data exposure.

## Required Controls

- `.gitignore`
- `.env.example`
- GitHub secret scanning
- YAML validation
- ShellCheck
- PSScriptAnalyzer for PowerShell
- PR checklist

## Never Commit

- `.env`
- Private keys
- API tokens
- Production inventory
- Cloudflare credentials
- Grafana database
- CrowdSec credentials