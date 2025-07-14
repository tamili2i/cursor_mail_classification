# User Service API Documentation

## Overview
This service provides user authentication and management for the Collaborative Document System. All endpoints are secured and return structured JSON responses.

## Authentication
- Uses JWT Bearer tokens for access and refresh.
- Register, login, and obtain tokens via `/auth/register` and `/auth/login`.
- Use the `access_token` in the `Authorization: Bearer <token>` header for protected endpoints.

## Endpoints

### Register
- `POST /auth/register`
- **Request:**
```json
{
  "email": "user@example.com",
  "password": "TestPassword1!",
  "full_name": "User Name"
}
```
- **Response:**
```json
{
  "id": "...",
  "email": "user@example.com",
  "full_name": "User Name",
  "is_active": true,
  "is_superuser": false,
  "created_at": "...",
  "updated_at": "..."
}
```
- **Errors:** 400 (already registered), 422 (validation)

### Login
- `POST /auth/login`
- **Request (form):**
```
username=user@example.com&password=TestPassword1!
```
- **Response:**
```json
{
  "access_token": "...",
  "refresh_token": "...",
  "token_type": "bearer"
}
```
- **Errors:** 401 (invalid credentials), 429/423 (rate limit/lockout)

### Get Profile
- `GET /auth/me`
- **Headers:** `Authorization: Bearer <access_token>`
- **Response:**
```json
{
  "id": "...",
  "email": "user@example.com",
  "full_name": "User Name",
  "is_active": true,
  "is_superuser": false,
  "created_at": "...",
  "updated_at": "..."
}
```

### Update Profile
- `PUT /auth/profile`
- **Headers:** `Authorization: Bearer <access_token>`
- **Request:**
```json
{
  "full_name": "New Name",
  "password": "NewPassword1!"
}
```
- **Response:** (same as Get Profile)

### Refresh Token
- `POST /auth/refresh`
- **Request:**
```json
{
  "refresh_token": "..."
}
```
- **Response:**
```json
{
  "access_token": "...",
  "refresh_token": "...",
  "token_type": "bearer"
}
```
- **Errors:** 401 (invalid/expired token)

### Logout
- `POST /auth/logout`
- **Headers:** `Authorization: Bearer <access_token>`
- **Request:**
```json
{
  "refresh_token": "..."
}
```
- **Response:**
```json
{
  "success": true,
  "data": {"message": "Logged out successfully."}
}
```

## Error Response Format
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Error message.",
    "details": {}
  }
}
```

## Security Features
- Rate limiting and account lockout
- Password complexity enforcement
- Audit logging
- Security headers and CORS
- Session management with Redis 