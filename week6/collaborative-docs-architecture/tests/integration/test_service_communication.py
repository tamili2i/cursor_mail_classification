import pytest
import asyncio
import httpx
import websockets

@pytest.mark.asyncio
async def test_service_communication():
    async with httpx.AsyncClient() as client:
        # Register user
        resp = await client.post("http://localhost/auth/register", json={
            "email": "integration@example.com",
            "password": "TestPassword1!",
            "full_name": "Integration Test"
        })
        assert resp.status_code in (200, 400)
        # Login
        resp = await client.post("http://localhost/auth/login", data={
            "username": "integration@example.com",
            "password": "TestPassword1!"
        })
        assert resp.status_code == 200
        tokens = resp.json()
        access_token = tokens["access_token"]
        # Create document
        resp = await client.post("http://localhost/documents/", json={
            "title": "Integration Doc",
            "content": "Hello"
        }, headers={"Authorization": f"Bearer {access_token}"})
        assert resp.status_code == 200
        doc_id = resp.json()["id"]
        # Collaborate via WebSocket
        ws_url = f"ws://localhost/ws/documents/{doc_id}?user_id=integration@example.com&username=Integration"
        async with websockets.connect(ws_url) as ws:
            join_event = await ws.recv()
            assert "user_joined" in join_event 