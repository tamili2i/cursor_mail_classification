# Document Service API Documentation

## Overview
This service provides collaborative document management with versioning, sharing, analytics, and export features. All endpoints require JWT Bearer authentication from the User Service.

## Authentication
- Use the `access_token` from the User Service in the `Authorization: Bearer <token>` header.

## Endpoints

### Create Document
- `POST /documents/`
- **Request:**
```json
{
  "title": "My Document",
  "content": "Initial content"
}
```
- **Response:**
```json
{
  "id": "...",
  "owner_id": "...",
  "title": "My Document",
  "content": "Initial content",
  "created_at": "...",
  "updated_at": "...",
  "is_deleted": false
}
```

### List Documents
- `GET /documents/`
- **Response:** List of documents owned by the user

### Get Document
- `GET /documents/{id}`
- **Response:** Document details

### Update Document
- `PUT /documents/{id}`
- **Request:**
```json
{
  "title": "Updated Title",
  "content": "Updated content"
}
```
- **Response:** Updated document

### Delete Document
- `DELETE /documents/{id}`
- **Response:** 204 No Content

### Get Versions
- `GET /documents/{id}/versions`
- **Response:** List of document versions

### Share Document
- `POST /documents/{id}/share`
- **Request:**
```json
{
  "user_ids": ["user1", "user2"],
  "permission": "read"
}
```
- **Response:** 204 No Content

### Get Collaborators
- `GET /documents/{id}/collaborators`
- **Response:** List of collaborators

### Search Documents
- `GET /documents/search?q=term`
- **Response:** List of search results

### File Upload
- `POST /documents/{id}/upload`
- **Request:** Multipart file upload
- **Response:** 204 No Content

### File Download
- `GET /documents/{id}/download`
- **Response:** File download

### Analytics
- `POST /documents/{id}/analytics`
- **Request:**
```json
{
  "event": "view",
  "user_id": "...",
  "timestamp": "...",
  "details": {}
}
```
- **Response:** 204 No Content
- `GET /documents/{id}/analytics` — List analytics events

### Backup & Restore
- `POST /documents/{id}/backup` — Backup document
- `POST /documents/{id}/restore` — Restore document

### Clone Document
- `POST /documents/{id}/clone` — Clone document for current user

### Export Document
- `GET /documents/{id}/export?format=pdf|docx|html` — Export document content

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

## Advanced Features
- Versioning with diff tracking
- Document sharing and permissions
- Full-text search (future)
- File upload/download
- Analytics and usage tracking
- Backup, restore, clone, export 