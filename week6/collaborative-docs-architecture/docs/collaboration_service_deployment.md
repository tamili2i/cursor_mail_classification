# Collaboration Service Deployment Guide

## Prerequisites
- Docker and Docker Compose installed
- Redis instance for event processing

## Quick Start (Development)
1. Clone the repository
2. Navigate to the project directory
3. Build and start all services:
   ```sh
   docker-compose up --build
   ```
4. The collaboration service will be available at ws://localhost:8000/ws/documents/{doc_id}

## Environment Variables
- `REDIS_URL`: Redis connection URL (e.g., `redis://redis:6379/0`)
- `CORS_ALLOW_ORIGINS`: Allowed CORS origins (default: `http://localhost`)
- `DOCUMENT_SERVICE_URL`: URL for Document Service integration (default: `http://document_service:8000`)

## Redis
- Used for event streaming, recovery, and distributed state
- Use a dedicated Redis instance in production

## Scaling and Load Balancing
- Run multiple instances behind a load balancer (Nginx, Traefik)
- Use sticky sessions or distributed presence via Redis for cross-instance sync
- Monitor `/metrics` endpoint for active connections and documents
- Tune worker count and async event loop settings for high concurrency

## Monitoring
- Scrape `/metrics` with Prometheus for real-time monitoring
- Set up alerts for connection drops, high latency, or errors

## Running in Production
- Set all secrets and connection strings via environment variables
- Use HTTPS and secure your infrastructure
- Monitor logs and metrics for security and performance
- Scale containers as needed

## Updating
- Pull latest code, rebuild containers:
   ```sh
   docker-compose down
   docker-compose up --build -d
   ``` 