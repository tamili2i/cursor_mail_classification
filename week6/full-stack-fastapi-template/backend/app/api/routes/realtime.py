from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from typing import Dict, List, Set
from uuid import UUID
from collections import defaultdict
import asyncio

router = APIRouter(prefix="/ws", tags=["realtime"])

# In-memory connection and notification store (for demo)
team_connections: Dict[UUID, Set[WebSocket]] = defaultdict(set)
user_connections: Dict[UUID, WebSocket] = dict()
offline_notifications: Dict[UUID, List[dict]] = defaultdict(list)
user_presence: Set[UUID] = set()

# Helper: broadcast to all team members
async def broadcast_team(team_id: UUID, message: dict):
    for ws in list(team_connections[team_id]):
        try:
            await ws.send_json(message)
        except Exception:
            team_connections[team_id].remove(ws)

# WebSocket endpoint for team collaboration
@router.websocket("/team/{team_id}")
async def team_ws(websocket: WebSocket, team_id: UUID, user_id: UUID):
    await websocket.accept()
    team_connections[team_id].add(websocket)
    user_presence.add(user_id)
    user_connections[user_id] = websocket
    # Send any queued notifications
    for note in offline_notifications[user_id]:
        await websocket.send_json(note)
    offline_notifications[user_id].clear()
    try:
        while True:
            data = await websocket.receive_json()
            event = data.get("event")
            payload = data.get("payload")
            # Broadcast task updates, notifications, activity, presence
            if event == "task_update":
                await broadcast_team(team_id, {"event": "task_update", "payload": payload})
            elif event == "notification":
                # Send to specific user if online, else queue
                target_id = payload.get("user_id")
                if target_id in user_connections:
                    await user_connections[target_id].send_json({"event": "notification", "payload": payload})
                else:
                    offline_notifications[target_id].append({"event": "notification", "payload": payload})
            elif event == "activity":
                await broadcast_team(team_id, {"event": "activity", "payload": payload})
            elif event == "presence":
                await broadcast_team(team_id, {"event": "presence", "payload": {"user_id": user_id, "status": "online"}})
    except WebSocketDisconnect:
        team_connections[team_id].remove(websocket)
        user_presence.discard(user_id)
        user_connections.pop(user_id, None)
        await broadcast_team(team_id, {"event": "presence", "payload": {"user_id": user_id, "status": "offline"}}) 