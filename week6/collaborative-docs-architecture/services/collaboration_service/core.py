import asyncio
from typing import Dict, Set
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.user_map: Dict[WebSocket, str] = {}
        self.lock = asyncio.Lock()

    async def connect(self, doc_id: str, websocket: WebSocket, user_id: str):
        await websocket.accept()
        async with self.lock:
            if doc_id not in self.active_connections:
                self.active_connections[doc_id] = set()
            self.active_connections[doc_id].add(websocket)
            self.user_map[websocket] = user_id

    async def disconnect(self, doc_id: str, websocket: WebSocket):
        async with self.lock:
            if doc_id in self.active_connections:
                self.active_connections[doc_id].discard(websocket)
                if not self.active_connections[doc_id]:
                    del self.active_connections[doc_id]
            self.user_map.pop(websocket, None)

    async def broadcast(self, doc_id: str, message: str):
        async with self.lock:
            for ws in self.active_connections.get(doc_id, set()):
                await ws.send_text(message)

    async def get_users(self, doc_id: str):
        async with self.lock:
            return [self.user_map[ws] for ws in self.active_connections.get(doc_id, set())]

manager = ConnectionManager() 