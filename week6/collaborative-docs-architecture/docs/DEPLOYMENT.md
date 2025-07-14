# Deployment Instructions

## Prerequisites
- Docker and Docker Compose installed

## Quick Start (Development)
1. Clone the repository
2. Navigate to the project directory
3. Build and start all services:
   ```sh
   docker-compose up --build
   ```
4. The user service will be available at http://localhost:8000

## Environment Variables
- See CONFIGURATION.md for all options
- Set secrets and connection strings in `docker-compose.yml` or via `.env` file

## Production Recommendations
- Set a strong `JWT_SECRET_KEY` and secure DB/Redis passwords
- Use HTTPS (behind a reverse proxy like Nginx or Traefik)
- Monitor logs and metrics
- Scale containers as needed

## Database Migrations
- Ensure the database is initialized before first run
- Alembic or manual migrations can be used for schema changes

## Updating
- Pull latest code, rebuild containers:
   ```sh
   docker-compose down
   docker-compose up --build -d
   ``` 