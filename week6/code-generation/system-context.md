# Collaborative Document System - Development Context
## Architecture Overview
- Microservices architecture with event-driven communication
- Real-time synchronization using WebSockets
- Operational transformation for conflict resolution
- Redis for caching and message queuing
- PostgreSQL for persistent data storage
## Code Standards
- FastAPI for all backend services
- Async/await patterns throughout
- Pydantic models for data validation
- Comprehensive error handling with custom exceptions
- OpenAPI documentation for all endpoints
## Integration Patterns
- Services communicate via Redis Streams
- All services expose health check endpoints
- Authentication via JWT tokens
- Standardized logging format
- Docker containerization for deployment
## Service Structure
Each service follows this pattern:
- main.py: FastAPI application setup
- models.py: Pydantic and SQLAlchemy models
- services.py: Business logic implementation
- routes.py: API endpoint definitions
- config.py: Configuration management
- tests/: Comprehensive test coverage