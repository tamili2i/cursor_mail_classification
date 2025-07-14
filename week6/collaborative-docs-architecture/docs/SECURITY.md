# Security Implementation Details

## Threat Model
- **Brute Force Attacks:** Prevented by rate limiting and account lockout.
- **Credential Stuffing:** Rate limiting and lockout mitigate automated attacks.
- **SQL Injection:** SQLAlchemy ORM and parameterized queries prevent injection.
- **XSS:** No user input is reflected in HTML; API responses are JSON only.
- **JWT Tampering:** Tokens are signed with a strong secret and validated on every request.
- **Session Hijacking:** Refresh tokens are stored in Redis and can be revoked on logout.
- **Replay Attacks:** Short-lived access tokens and refresh token rotation.

## Security Features & Mitigations

### Rate Limiting
- All authentication endpoints are rate limited per user and per IP.
- Configurable via environment variables.
- Exceeding limits returns HTTP 429.

### Account Lockout
- After N failed login attempts, the account is locked for a configurable duration.
- Locked accounts return HTTP 423.

### Password Policy
- Minimum 8 characters, max 128.
- Must include uppercase, lowercase, digit, and special character.
- Enforced via Pydantic validators.

### Audit Logging
- All security-relevant events (login, failed login, registration, password change, logout, lockout) are logged with user, IP, user agent, and timestamp.
- Logs are structured for compliance and monitoring.

### Session Management
- Refresh tokens are stored in Redis with expiration.
- Logout and token refresh revoke old tokens.
- Session invalidation is immediate on logout.

### Security Headers
- HSTS, X-Frame-Options, X-Content-Type-Options, Referrer-Policy, CSP, and Permissions-Policy are set on all responses.

### CORS
- Origins are restricted and configurable via environment variable.

## Best Practices
- Use HTTPS in production.
- Rotate JWT secret and database credentials regularly.
- Monitor audit logs for suspicious activity.
- Set strong, unique environment secrets for JWT and database.
- Regularly update dependencies to patch vulnerabilities. 