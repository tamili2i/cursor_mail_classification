# Document Service Deployment Guide

## Prerequisites
- Docker and Docker Compose installed

## Quick Start (Development)
1. Clone the repository
2. Navigate to the project directory
3. Build and start all services:
   ```sh
   docker-compose up --build
   ```
4. The document service will be available at http://localhost:8000

## Environment Variables
- `POSTGRES_DSN`: PostgreSQL DSN (e.g., `postgresql+asyncpg://user:password@db:5432/userdb`)
- `REDIS_URL`: Redis connection URL (e.g., `redis://redis:6379/0`)
- `JWT_SECRET_KEY`: Secret for JWT validation (must match User Service)
- `JWT_ALGORITHM`: JWT algorithm (default: HS256)
- `CORS_ALLOW_ORIGINS`: Allowed CORS origins (default: `http://localhost`)

## Database
- Uses PostgreSQL with asyncpg driver
- Database and user must be created before running the service

## Redis
- Used for caching documents and search results
- Use a dedicated Redis instance in production

## Running in Production
- Set all secrets and connection strings via environment variables
- Use HTTPS and secure your infrastructure
- Monitor logs and metrics for security events
- Scale containers as needed

## Updating
- Pull latest code, rebuild containers:
   ```sh
   docker-compose down
   docker-compose up --build -d
   ```

## Additional Notes
- Ensure the JWT secret and algorithm match the User Service for authentication to work
- For file upload/download, ensure the `files/` directory is writable and persistent if needed
- For export features, install and configure any required libraries (e.g., for PDF/DOCX) 