# Seat Allocation System

A comprehensive system for managing employee seating, team assignments, and meeting room bookings within a multi-floor office environment.

## Features

- **Team Management**: Group employees into teams and manage team assignments
- **Seat Allocation**: Allocate seats to employees with workbench capacity management
- **Meeting Room Booking**: Book and manage meeting rooms
- **Floor Management**: Handle multiple floors and their layouts
- **SSO Integration**: Secure authentication with company email (Gmail/Outlook)
- **Position-based Allocation**: Special room allocation for higher positions

## System Requirements

- Python 3.8+
- Node.js 16+
- PostgreSQL 14+
- Redis (optional, for caching)

## Architecture

The system follows a microservices architecture with the following components:

```
+------------------+     +------------------+     +------------------+
|                  |     |                  |     |                  |
|  Client Layer    |     |  API Gateway     |     |  Auth Service    |
|  (React SPA)     |<--->|  (FastAPI)       |<--->|  (SSO)           |
|                  |     |                  |     |                  |
+------------------+     +------------------+     +------------------+
                                |
                                |
        +------------------+    |    +------------------+
        |                  |    |    |                  |
        |  Seat Service    |<---+--->|  Team Service    |
        |                  |    |    |                  |
        +------------------+    |    +------------------+
                |               |               |
                |               |               |
        +------------------+    |    +------------------+
        |                  |    |    |                  |
        |  Meeting Service |<---+--->|  Employee Service|
        |                  |    |    |                  |
        +------------------+    |    +------------------+
                |               |               |
                |               |               |
                v               v               v
        +--------------------------------------------------+
        |                                                  |
        |               PostgreSQL Database                |
        |                                                  |
        +--------------------------------------------------+
```

## Technology Stack

### Backend
- FastAPI
- SQLAlchemy
- Alembic
- Pydantic
- Python-jose
- Passlib
- pytest

### Frontend
- React 18
- TypeScript
- Redux Toolkit
- React Query
- Material-UI
- React Router
- Jest

### Database
- PostgreSQL
- Redis (optional)

### DevOps
- Docker
- Docker Compose
- GitHub Actions
- Nginx

## Installation

1. Clone the repository:
```bash
git clone [repository-url]
cd tesl2
```

2. Set up the backend:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Set up the frontend:
```bash
cd frontend
npm install
```

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Start the development servers:
```bash
# Backend
cd backend
uvicorn main:app --reload

# Frontend
cd frontend
npm start
```

## API Documentation

The API documentation is available at `/docs` when running the backend server.

### Key Endpoints

#### Authentication
- `POST /api/auth/login`
- `POST /api/auth/logout`
- `GET /api/auth/me`

#### Teams
- `GET /api/teams`
- `POST /api/teams`
- `GET /api/teams/{team_id}`
- `PUT /api/teams/{team_id}`
- `DELETE /api/teams/{team_id}`

#### Employees
- `GET /api/employees`
- `POST /api/employees`
- `GET /api/employees/{employee_id}`
- `PUT /api/employees/{employee_id}`
- `DELETE /api/employees/{employee_id}`

#### Seats
- `GET /api/seats`
- `POST /api/seats/allocate`
- `PUT /api/seats/{seat_id}`
- `DELETE /api/seats/{seat_id}`
- `GET /api/seats/available`

#### Meeting Rooms
- `GET /api/meeting-rooms`
- `POST /api/meeting-rooms`
- `GET /api/meeting-rooms/{room_id}`
- `PUT /api/meeting-rooms/{room_id}`
- `DELETE /api/meeting-rooms/{room_id}`

#### Bookings
- `GET /api/bookings`
- `POST /api/bookings`
- `GET /api/bookings/{booking_id}`
- `PUT /api/bookings/{booking_id}`
- `DELETE /api/bookings/{booking_id}`

## Database Schema

The system uses PostgreSQL with the following main tables:

- users
- teams
- floors
- workbenches
- seats
- meeting_rooms
- meeting_bookings

For detailed schema information, refer to the `migrations` directory.

## Development

### Running Tests

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

### Code Style

The project follows PEP 8 for Python and ESLint for JavaScript/TypeScript.

## Deployment

1. Build the frontend:
```bash
cd frontend
npm run build
```

2. Build and run with Docker:
```bash
docker-compose up --build
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

[Your License Here]

## Support

For support, please contact [Your Contact Information] 