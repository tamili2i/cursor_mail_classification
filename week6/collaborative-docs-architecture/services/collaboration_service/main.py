import os
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import json
from .core import manager
from .events import (
    USER_JOINED, USER_LEFT, DOCUMENT_CHANGE, CURSOR_POSITION, DOCUMENT_SAVED, PRESENCE, ATTRIBUTION, RECOVERY,
    UserJoinedEvent, UserLeftEvent, DocumentChangeEvent, CursorPositionEvent, DocumentSavedEvent, PresenceEvent, AttributionEvent, RecoveryEvent, EventEnvelope
)
from collections import defaultdict
import time
from fastapi.responses import PlainTextResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("collaboration_service")

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; object-src 'none'; frame-ancestors 'none'; base-uri 'self';"
        )
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        return response

app = FastAPI(
    title="Collaboration Service",
    description="Real-time collaborative editing service",
    version="1.0.0"
)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("CORS_ALLOW_ORIGINS", "http://localhost").split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

presence_map = defaultdict(dict)  # doc_id -> {user_id: {username, cursor, last_seen}}

@app.websocket("/ws/documents/{doc_id}")
async def websocket_endpoint(websocket: WebSocket, doc_id: str):
    user_id = websocket.query_params.get("user_id", "anonymous")
    username = websocket.query_params.get("username", user_id)
    await manager.connect(doc_id, websocket, user_id)
    try:
        # Add to presence
        presence_map[doc_id][user_id] = {"username": username, "cursor": 0, "last_seen": time.time()}
        # Broadcast join and presence
        join_event = UserJoinedEvent(user_id=user_id, username=username)
        await manager.broadcast(doc_id, join_event.json())
        presence_event = PresenceEvent(users=[{"user_id": uid, **info} for uid, info in presence_map[doc_id].items()])
        await manager.broadcast(doc_id, presence_event.json())
        while True:
            data = await websocket.receive_text()
            try:
                event = json.loads(data)
                event_type = event.get("type")
                if event_type == DOCUMENT_CHANGE:
                    change_event = DocumentChangeEvent(**event)
                    # Attribution: broadcast who made the change
                    attribution_event = AttributionEvent(changes=[{"user_id": user_id, "op": change_event.op, "timestamp": change_event.timestamp}])
                    await manager.broadcast(doc_id, change_event.json())
                    await manager.broadcast(doc_id, attribution_event.json())
                elif event_type == CURSOR_POSITION:
                    cursor_event = CursorPositionEvent(**event)
                    # Update presence with cursor
                    presence_map[doc_id][user_id]["cursor"] = cursor_event.position
                    presence_map[doc_id][user_id]["last_seen"] = time.time()
                    await manager.broadcast(doc_id, cursor_event.json())
                    # Broadcast updated presence
                    presence_event = PresenceEvent(users=[{"user_id": uid, **info} for uid, info in presence_map[doc_id].items()])
                    await manager.broadcast(doc_id, presence_event.json())
                # Add more event types as needed
            except Exception as e:
                await websocket.send_text(json.dumps({"type": "error", "message": str(e)}))
    except WebSocketDisconnect:
        await manager.disconnect(doc_id, websocket)
        # Remove from presence
        presence_map[doc_id].pop(user_id, None)
        leave_event = UserLeftEvent(user_id=user_id)
        await manager.broadcast(doc_id, leave_event.json())
        # Broadcast updated presence
        presence_event = PresenceEvent(users=[{"user_id": uid, **info} for uid, info in presence_map[doc_id].items()])
        await manager.broadcast(doc_id, presence_event.json())
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        logger.info(f"Active connections for doc {doc_id}: {len(manager.active_connections.get(doc_id, []))}")

@app.get("/metrics", response_class=PlainTextResponse)
async def metrics():
    # Prometheus-style metrics
    lines = []
    total_docs = len(manager.active_connections)
    total_connections = sum(len(conns) for conns in manager.active_connections.values())
    lines.append(f"collab_active_documents {total_docs}")
    lines.append(f"collab_active_connections {total_connections}")
    for doc_id, conns in manager.active_connections.items():
        lines.append(f'collab_document_connections{{doc_id="{doc_id}"}} {len(conns)}')
    return "\n".join(lines)

@app.get("/health", tags=["Health"])
async def health_check():
    return {"success": True, "data": {"status": "ok"}}

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled error: {exc}")
    return PlainTextResponse(f"Internal server error: {exc}", status_code=500)
