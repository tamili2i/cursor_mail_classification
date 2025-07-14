# System Context for Collaborative Document System

This document defines the system context, development standards, integration specifications, and quality requirements for the collaborative document system. It is intended to guide consistent, production-ready code generation across all microservices.

---

## 1. Architecture Overview

### Microservices

- **UserService**: Handles user registration, authentication, profile management, and user-related data.
- **DocumentService**: Manages document CRUD operations, versioning, and storage.
- **CollaborationService**: Orchestrates real-time collaboration, tracks editing sessions, and manages concurrent updates.

### Communication

- **REST APIs**: All services expose RESTful endpoints for standard operations.
- **WebSocket**: CollaborationService provides WebSocket endpoints for real-time document editing and presence updates.
- **Service-to-Service**: Internal REST calls or message passing via Redis Pub/Sub for event-driven actions.

### Data Storage

- **PostgreSQL**: Primary data store for persistent entities (users, documents, permissions, etc.).
- **Redis**: Used for caching, rate limiting, session management, and Pub/Sub messaging for real-time collaboration.

### Tech Stack

- **Framework**: FastAPI (Python)
- **ORM**: SQLAlchemy
- **Cache/Messaging**: Redis
- **Real-Time**: WebSockets (via FastAPI)
- **Testing**: Pytest, HTTPX, pytest-asyncio

---

## 2. Development Standards

### Code Structure & Patterns

- **Modular Design**: Each service is a standalone FastAPI app with clear separation of routers, models, schemas, services, and utils.
- **Directory Layout**:
  ```
  app/
    main.py
    models/
    schemas/
    services/
    routes/
    utils/
    tests/
  ```
- **Dependency Injection**: Use FastAPI's dependency injection for DB sessions, authentication, and configuration.
- **Async-first**: All I/O operations (DB, Redis, HTTP) must be async.

### Error Handling

- **Consistent Exception Handling**: Use FastAPI exception handlers for HTTP errors.
- **Custom Error Responses**: Return structured error objects with `code`, `message`, and optional `details`.
- **Logging**: Log all errors with context (user, request, stack trace).

### API Response Formats

- **Success**:
  ```json
  {
    "success": true,
    "data": { ... }
  }
  ```
- **Error**:
  ```json
  {
    "success": false,
    "error": {
      "code": "ERROR_CODE",
      "message": "Human-readable message",
      "details": { ... }
    }
  }
  ```
- **Validation Errors**: Use FastAPI's validation error format, but wrap in the above error structure.

### Database Model Patterns

- **SQLAlchemy ORM**: Use declarative models with type annotations.
- **Timestamps**: All models include `created_at` and `updated_at` fields.
- **Soft Deletes**: Use a `deleted` boolean flag where appropriate.
- **Relationships**: Use explicit foreign keys and backrefs.

### Testing Requirements

- **Coverage**: Minimum 90% code coverage for business logic.
- **Types**: Use type hints and enforce with mypy.
- **Test Types**: Unit, integration, and API contract tests.
- **Fixtures**: Use pytest fixtures for DB, Redis, and test clients.
- **CI**: All tests must pass in CI before merge.

---

## 3. Integration Specifications

### Service Communication Protocols

- **REST**: JSON over HTTP, versioned endpoints (`/v1/`).
- **WebSocket**: JSON messages, authenticated via JWT in query params or headers.
- **Redis Pub/Sub**: Channel naming: `collab:<doc_id>`, message format: JSON.

### Authentication & Authorization

- **JWT**: All APIs require Bearer JWT tokens, issued by UserService.
- **Password Hashing**: Use bcrypt via passlib.
- **Rate Limiting**: Enforced via Redis (per user/email).
- **Role-Based Access**: Permissions checked per endpoint (owner, editor, viewer).

### Data Validation

- **Pydantic Schemas**: All request/response bodies validated with Pydantic.
- **Strict Types**: No implicit type coercion.
- **Email/Password**: Use Pydantic's EmailStr, enforce password policies.

### Real-Time Message Formats

- **Edit Event**:
  ```json
  {
    "type": "edit",
    "user_id": "uuid",
    "doc_id": "uuid",
    "changes": { ... },
    "timestamp": "ISO8601"
  }
  ```
- **Presence Event**:
  ```json
  {
    "type": "presence",
    "user_id": "uuid",
    "doc_id": "uuid",
    "status": "joined|left|active",
    "timestamp": "ISO8601"
  }
  ```
- **Error Event**:
  ```json
  {
    "type": "error",
    "code": "ERROR_CODE",
    "message": "Human-readable message"
  }
  ```

---

## 4. Quality Requirements

### Performance

- **API Latency**: < 200ms p95 for standard requests.
- **WebSocket**: Real-time events delivered < 100ms p95.
- **Scalability**: Services stateless, ready for horizontal scaling.

### Security

- **Input Validation**: All inputs validated and sanitized.
- **Authentication**: JWT required for all endpoints.
- **Authorization**: Enforced at route and business logic level.
- **Rate Limiting**: Per user/IP, enforced via Redis.
- **Sensitive Data**: Never log passwords or tokens.

### Logging & Monitoring

- **Structured Logging**: JSON logs with timestamp, service, level, request_id, user_id.
- **Error Tracking**: Integrate with Sentry or similar.
- **Metrics**: Expose Prometheus metrics endpoint (`/metrics`).
- **Audit Logs**: Track document edits, user logins, permission changes.

### Documentation

- **OpenAPI**: All APIs documented via FastAPI's auto-generated docs.
- **Docstrings**: All public functions/classes have docstrings.
- **README**: Each service includes setup, usage, and API reference.
- **Changelog**: Maintain a changelog for each service.

---

**AI Driven Development #60day challenge**: All code, tests, and documentation must be generated and reviewed with AI assistance, ensuring consistency, best practices, and rapid iteration.

---
