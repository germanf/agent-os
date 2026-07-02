# HTTP Basic Authentication

The dashboard is protected by HTTP Basic Authentication to prevent unauthorized access and Remote Code Execution (RCE) attacks.

## Configuration

### Environment Variables

Set the following environment variables to enable authentication:

```bash
DASH_USER=your-username
DASH_PASS=your-secure-password
```

### On the Production VM

Edit the systemd service file or add to `start.sh`:

```bash
export DASH_USER="your-username"
export DASH_PASS="your-secure-password"
```

Alternatively, set them in the systemd service environment:

```bash
sudo systemctl edit agentic-software-boutique
```

Add to the `[Service]` section:

```ini
Environment="DASH_USER=your-username"
Environment="DASH_PASS=your-secure-password"
```

## How It Works

- **Authentication Method:** HTTP Basic Auth (RFC 7617)
- **Credentials Format:** `Authorization: Basic base64(username:password)`
- **Public Endpoints:**
  - `/api/health` — Health check (no auth required)
  - `/auth/callback` — OAuth callback from X.com (no auth required)
- **Protected Endpoints:** All other routes require valid credentials

The browser caches credentials automatically, so you only need to enter them once on first access. The authentication applies to:
- All `/api/*` routes (credentials management, jobs, chat, files, notes, etc.)
- The SPA fallback route (`/`) — triggers the browser's native auth dialog on first load
- `/auth/start` — Initiates OAuth flow (auth header cached by browser)

## Client Examples

### Using curl

```bash
# With credentials in the command
curl -u "username:password" http://localhost:8765/api/health

# With Authorization header (base64-encoded)
curl -H "Authorization: Basic $(echo -n 'username:password' | base64)" \
     http://localhost:8765/api/credentials
```

### Using JavaScript/Fetch

The browser automatically includes cached credentials for same-origin requests:

```javascript
// First request triggers browser auth dialog
const response = await fetch('/api/chat/send', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ message: 'Hello' }),
});

// Subsequent requests use cached credentials
```

For **EventSource** (chat streaming), credentials are automatically included:

```javascript
// Browser caches auth, EventSource automatically includes credentials
const eventSource = new EventSource('/api/jobs/xyz/stream');
eventSource.onmessage = (e) => { /* ... */ };
```

### Using fetch with explicit credentials (if not cached)

```javascript
const credentials = btoa('username:password');
const response = await fetch('/api/chat/send', {
  method: 'POST',
  headers: {
    'Authorization': `Basic ${credentials}`,
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({ message: 'Hello' }),
});
```

## Changing Credentials

1. Update the environment variables:
   ```bash
   export DASH_USER="new-username"
   export DASH_PASS="new-password"
   ```

2. Restart the dashboard:
   ```bash
   # On production VM
   systemctl restart agentic-software-boutique
   
   # Or locally
   ./start.sh
   ```

3. Clear browser cache (the browser's HTTP Auth dialog will appear again)

## Security Considerations

- **HTTPS Recommended:** In production, use HTTPS to prevent credentials from being transmitted in plaintext over the network
- **Strong Passwords:** Use a strong, randomly generated password
- **Environment Variables:** Never commit real credentials to git; use `.env.example` as a template
- **Timing-Safe Comparison:** Credentials are compared using `secrets.compare_digest()` to prevent timing attacks
- **Limited Scope:** This is a simple auth mechanism suitable for a dashboard behind a VPN. For public internet exposure, consider:
  - OAuth 2.0 with a proper identity provider
  - JWT tokens
  - Mutual TLS (mTLS)

## Troubleshooting

### Browser keeps prompting for credentials
- The browser's auth dialog appears if:
  - Credentials are not yet cached
  - The credentials provided are incorrect
  - The browser session ended or was cleared
- **Solution:** Enter the correct credentials once; the browser will cache them for subsequent requests

### 401 Unauthorized errors
- **Check:** Verify the `DASH_USER` and `DASH_PASS` environment variables are set correctly
- **Check:** Confirm the auth header is properly formatted: `Authorization: Basic <base64(username:password)>`
- **Check:** The base64 encoding is correct

### EventSource failing with 401
- **Cause:** Browser didn't cache credentials, or cached credentials are invalid
- **Solution:** Ensure you can access the main page (`/`) without a 401 error; this caches credentials for subsequent requests

## Testing

Run the test suite to verify authentication:

```bash
cd dashboard
python3 -m pytest tests/test_http_auth.py -v
# or
python3 tests/test_http_auth.py
```

Tests verify:
- Health check works without auth
- API endpoints return 401 without credentials
- API endpoints work with correct credentials
- Invalid credentials are rejected
- Malformed auth headers are rejected
- OAuth callback works without auth
