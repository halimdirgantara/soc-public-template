# Cloudflare Notes

This public repository does not include Cloudflare credentials.

Do not commit:

- Tunnel credentials JSON
- Account IDs if sensitive
- API tokens
- Production tunnel IDs
- Real DNS topology

## Recommended Pattern

For public services behind Cloudflare or a reverse proxy:

1. Preserve real client IP using `CF-Connecting-IP` or `X-Forwarded-For`.
2. Confirm backend logs show the client IP, not only proxy IP.
3. Use host-level CrowdSec bouncer only when it can see the correct source IP.
4. For Cloudflare-proxied traffic, consider Cloudflare bouncer in the private repository.