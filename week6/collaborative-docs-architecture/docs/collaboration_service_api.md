# Collaboration Service API Documentation

## Overview
This service provides real-time collaborative editing for documents using WebSockets, Operational Transformation, and Redis Streams. All endpoints require JWT Bearer authentication (in production).

## WebSocket Endpoint
- `ws://<host>/ws/documents/{doc_id}?user_id=<user_id>&username=<username>`
- Connect to this endpoint to join a collaborative editing session for a document.

## Authentication
- In production, use JWT Bearer tokens for authentication (pass as query param or header).

## WebSocket Events

### user_joined
```json
{
  "type": "user_joined",
  "user_id": "user1",
  "username": "User1"
}
```

### user_left
```json
{
  "type": "user_left",
  "user_id": "user1"
}
```

### document_change
```json
{
  "type": "document_change",
  "user_id": "user1",
  "op": {"op_type": "insert", "pos": 0, "text": "A"},
  "version": 1,
  "timestamp": 123.0
}
```

### cursor_position
```json
{
  "type": "cursor_position",
  "user_id": "user1",
  "position": 5
}
```

### document_saved
```json
{
  "type": "document_saved",
  "user_id": "user1",
  "version": 2,
  "timestamp": 124.0
}
```

### presence
```json
{
  "type": "presence",
  "users": [
    {"user_id": "user1", "username": "User1", "cursor": 5, "last_seen": 123.0},
    {"user_id": "user2", "username": "User2", "cursor": 0, "last_seen": 123.1}
  ]
}
```

### attribution
```json
{
  "type": "attribution",
  "changes": [
    {"user_id": "user1", "op": {"op_type": "insert", "pos": 0, "text": "A"}, "timestamp": 123.0}
  ]
}
```

### recovery
```json
{
  "type": "recovery",
  "state": {"text": "current doc text", "version": 5, "history": [...]}
}
```

### Error Event
```json
{
  "type": "error",
  "message": "Error message"
}
```

## Metrics Endpoint
- `GET /metrics` — Prometheus-style metrics for active documents and connections

## Advanced Features
- Operational Transformation for conflict resolution
- Real-time presence and attribution
- Redis Streams for event recovery and replay
- Undo/redo, recovery, and network failure handling

## Usage Pattern
1. Connect to the WebSocket endpoint with your user ID and username
2. Listen for `user_joined`, `presence`, and `document_change` events
3. Send `document_change` and `cursor_position` events as you edit
4. Handle `attribution`, `recovery`, and `error` events as needed 