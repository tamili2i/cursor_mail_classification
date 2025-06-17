# User Management Microservice

A robust user management microservice built with FastAPI, PostgreSQL, and modern Python practices.

## Features

- RESTful API with proper HTTP methods
- PostgreSQL database with connection pooling
- JWT-based authentication
- Input validation using Pydantic
- Comprehensive error handling
- Structured logging
- Unit tests
- Database migrations with Alembic

## Prerequisites

- Python 3.8+
- PostgreSQL 12+
- pip (Python package manager)

## Project Structure

```
user_management_service/
├── app/
│   ├── api/            # API routes and endpoints
│   ├── core/           # Core configurations
│   ├── db/             # Database configurations
│   ├── models/         # SQLAlchemy models
│   ├── schemas/        # Pydantic schemas
│   ├── services/       # Business logic
│   └── utils/          # Utility functions
├── tests/              # Test files
├── alembic/            # Database migrations
├── .env                # Environment variables
├── requirements.txt    # Project dependencies
└── README.md          # Project documentation
```

## Setup Instructions

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd user_management_service
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   Create a `.env` file in the root directory with the following variables:
   ```
   DATABASE_URL=postgresql://user:password@localhost:5432/user_management
   SECRET_KEY=your-secret-key
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   ```

5. Initialize the database:
   ```bash
   alembic upgrade head
   ```

6. Run the application:
   ```bash
   uvicorn app.main:app --reload
   ```

## API Endpoints

### Authentication
- POST `/api/v1/auth/login` - User login
- POST `/api/v1/auth/refresh` - Refresh access token

### Users
- POST `/api/v1/users` - Create new user
- GET `/api/v1/users` - List all users
- GET `/api/v1/users/{user_id}` - Get user details
- PUT `/api/v1/users/{user_id}` - Update user
- DELETE `/api/v1/users/{user_id}` - Delete user

## Running Tests

```bash
pytest
```

## Development

1. Create a new branch for your feature
2. Make your changes
3. Write/update tests
4. Submit a pull request

## Error Handling

The service implements comprehensive error handling with proper HTTP status codes and descriptive error messages.

## Logging

Logs are written to both console and file with different log levels for development and production environments.

## Security

- Password hashing using bcrypt
- JWT token-based authentication
- Input validation
- SQL injection prevention
- CORS configuration

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request 