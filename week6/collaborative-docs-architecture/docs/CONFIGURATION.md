# Configuration Guide

This document describes how to configure the User Service for different environments.

## Environment Variables

| Variable                        | Description                                      | Default                                      |
|----------------------------------|--------------------------------------------------|----------------------------------------------|
| `JWT_SECRET_KEY`                | Secret key for signing JWT tokens                | `supersecretkey` (change in production!)     |
| `JWT_ALGORITHM`                 | JWT signing algorithm                            | `HS256`                                      |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | Access token expiry (minutes)                   | `30`                                         |
| `JWT_REFRESH_TOKEN_EXPIRE_MINUTES`| Refresh token expiry (minutes)                  | `10080` (7 days)                             |
| `POSTGRES_DSN`                  | PostgreSQL DSN for SQLAlchemy                    | `postgresql+asyncpg://user:password@localhost:5432/userdb` |
| `REDIS_URL`                     | Redis connection URL                             | `redis://localhost:6379/0`                   |
| `RATE_LIMIT_ATTEMPTS`           | Max attempts per window (rate limiting)          | `5`                                          |
| `RATE_LIMIT_WINDOW`             | Rate limit window (seconds)                      | `60`                                         |
| `ACCOUNT_LOCKOUT_ATTEMPTS`      | Failed login attempts before lockout             | `10`                                         |
| `ACCOUNT_LOCKOUT_DURATION`      | Lockout duration (seconds)                       | `900` (15 min)                               |
| `CORS_ALLOW_ORIGINS`            | Comma-separated allowed origins for CORS         | `http://localhost,http://127.0.0.1`           |

## Database
- Use PostgreSQL with the asyncpg driver.
- Example DSN: `postgresql+asyncpg://user:password@localhost:5432/userdb`
- Create the database and user before running the service.

## Redis
- Used for rate limiting, session management, and account lockout.
- Example URL: `redis://localhost:6379/0`
- Use a dedicated Redis instance in production.

## CORS
- Restrict allowed origins in production using `CORS_ALLOW_ORIGINS`.
- Example: `CORS_ALLOW_ORIGINS=https://yourdomain.com`

## Secrets
- Always set a strong, unique `JWT_SECRET_KEY` in production.
- Store secrets securely (e.g., environment variables, secret manager).

## Running in Development
- Defaults are suitable for local development.
- Use Docker Compose for easy setup (see deployment instructions).

## Running in Production
- Set all secrets and connection strings via environment variables.
- Use HTTPS and secure your infrastructure.
- Monitor logs and metrics for security events. 