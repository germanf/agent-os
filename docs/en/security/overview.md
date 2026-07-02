# Security

## Authentication

HTTP Basic Authentication is enforced at the application layer:

- **Credentials**: `DASH_USER` and `DASH_PASS` environment variables, or `dashboard/.credentials.json`
- **Storage**: Files are gitignored with `chmod 0600` permissions
- **Comparison**: Timing-safe via `hmac.compare_digest()`
- **Exception**: `/api/health` is accessible without authentication

## Network Security

- **VPN-only**: nginx allows traffic only from `10.0.0.0/24` subnet
- **Firewall**: iptables rules persisted via netfilter-persistent
- **TLS**: Self-signed certificate for HTTPS; replace with CA cert for public access
- **HSTS**: `Strict-Transport-Security` header with `max-age=31536000`

## Secrets Management

- Credential files (`.credentials.json`, `.env`) are gitignored
- API secrets are masked as `••••••••` when returned from GET endpoints
- POST endpoints preserve existing values when masked values are submitted
- Never hardcode credentials in source files
- Never log credential values

## XSS Prevention

- All rendered Markdown content is sanitized via **DOMPurify**
- `rel="noopener noreferrer"` enforced on all `target="_blank"` links
- Strict allowlist of HTML tags and attributes

## File Upload Security

- Max file size: 10 MB per file
- Max total: 50 MB across all files in a request
- Max file count: 10 files per request
- Validated by FastAPI before storage
- nginx `client_max_body_size` set to 55 MB (headroom above app limit)

## Rate Limiting

- Every API endpoint has a per-minute rate limit
- Typical limits: 30/min for reads, 10/min for mutations
- Health check: 60/min
- Prevents abuse and brute-force attacks

## Responsible Disclosure

If you discover a security vulnerability, please open a GitHub issue with the `security` label. Do not disclose vulnerabilities publicly until they have been addressed.

## Recommendations

1. Use strong passwords (32+ characters recommended for internet-facing instances)
2. Rotate credentials regularly
3. Keep the VPN-only restriction in production
4. Replace self-signed TLS certificate with a CA-signed one for public access
5. Regularly update dependencies
6. Monitor `/api/alerts` for security-related alerts
