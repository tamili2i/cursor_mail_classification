# Task Management System (Asana-like)

A scalable, real-time task management platform inspired by Asana. Built with FastAPI, PostgreSQL, and React, supporting team collaboration, project management, and analytics.

---

## Features
- **User Authentication & Team Management**
- **Project Creation with Tasks & Subtasks**
- **Real-Time Collaboration & Notifications**
- **File Attachments & Comments**
- **Dashboard with Analytics**

---

## System Architecture
- **Frontend:** React (TypeScript)
- **Backend:** FastAPI (Python)
- **Database:** PostgreSQL
- **Real-Time:** WebSockets (FastAPI + Redis Pub/Sub)
- **File Storage:** S3-compatible Object Storage
- **Microservices-ready:** Modular backend services
- **Containerization:** Docker, Docker Compose

```
[React App] ⇄ [FastAPI API Gateway] ⇄ [Microservices: Auth, User/Team, Project/Task, Notification, File, Analytics, WebSocket] ⇄ [PostgreSQL, Redis, S3]
```

---

## Database Schema (Overview)
- **users**: id, email, password_hash, name, ...
- **teams**: id, name, owner_id
- **team_members**: id, team_id, user_id, role
- **projects**: id, name, description, team_id, created_by, created_at
- **tasks**: id, project_id, parent_task_id, title, description, status, assignee_id, due_date, priority, created_by, created_at
- **task_comments**: id, task_id, user_id, comment, created_at
- **task_attachments**: id, task_id, file_url, uploaded_by, uploaded_at
- **notifications**: id, user_id, type, data, read, created_at
- **activity_logs**: id, user_id, action, entity_type, entity_id, data, created_at

---

## API Endpoints (Sample)

**Auth**
- `POST /auth/signup`
- `POST /auth/login`
- `POST /auth/logout`

**Teams**
- `GET /teams`
- `POST /teams`
- `POST /teams/{team_id}/invite`

**Projects**
- `GET /projects`
- `POST /projects`

**Tasks**
- `GET /projects/{project_id}/tasks`
- `POST /projects/{project_id}/tasks`
- `POST /tasks/{task_id}/subtasks`
- `POST /tasks/{task_id}/comment`
- `POST /tasks/{task_id}/attachment`

**Notifications**
- `GET /notifications`

**WebSocket**
- `GET /ws/notifications`
- `GET /ws/project/{project_id}`

---

## Real-Time Communication Strategy
- **WebSocket Service:** FastAPI WebSocket endpoints for real-time updates.
- **Channels:** Project updates, task changes, comments, notifications.
- **Backend:** Redis Pub/Sub for message brokering between services and WebSocket server.
- **Frontend:** Subscribes to relevant channels for instant updates.

---

## Performance Optimization Plan
- **Database:** Indexes, partitioning, read replicas.
- **Backend:** Async endpoints, connection pooling, Redis caching, background tasks.
- **WebSocket:** Redis pub/sub, horizontal scaling.
- **File Storage:** S3 + CDN.
- **Microservices:** Stateless, containerized, API Gateway, service discovery.
- **Frontend:** Efficient state management, lazy loading, batching.
- **Monitoring:** Centralized logging, metrics, health checks, auto-scaling.

---

## Tech Stack
- **Backend:** FastAPI, SQLAlchemy, Alembic, Redis, Celery
- **Frontend:** React, TypeScript, WebSockets
- **Database:** PostgreSQL
- **File Storage:** S3 (MinIO, AWS S3, etc.)
- **Containerization:** Docker
- **Testing:** Pytest, Playwright

---

## Setup Instructions

### Prerequisites
- Docker & Docker Compose
- Node.js (for frontend development)
- Python 3.10+

### Quick Start
1. **Clone the repository:**
   ```bash
   git clone <repo-url>
   cd <project-directory>
   ```
2. **Start services:**
   ```bash
   docker-compose up --build
   ```
3. **Access the app:**
   - Frontend: [http://localhost:3000](http://localhost:3000)
   - Backend API: [http://localhost:8000/docs](http://localhost:8000/docs)

### Development
- **Backend:**
  - `cd backend`
  - `uvicorn app.main:app --reload`
- **Frontend:**
  - `cd frontend`
  - `npm install && npm run dev`

---

## Contribution Guidelines
1. Fork the repo and create your branch (`git checkout -b feature/your-feature`)
2. Commit your changes (`git commit -am 'Add new feature'`)
3. Push to the branch (`git push origin feature/your-feature`)
4. Create a Pull Request

---

## License
MIT 