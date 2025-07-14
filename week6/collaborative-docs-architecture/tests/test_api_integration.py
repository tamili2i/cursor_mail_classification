import pytest
import asyncio
from httpx import AsyncClient
from week6.collaborative_docs_architecture.services.user_service.main import app

@pytest.mark.asyncio
async def test_register_and_login(monkeypatch):
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Register
        resp = await ac.post("/auth/register", json={
            "email": "integration@example.com",
            "password": "TestPassword1!",
            "full_name": "Integration Test"
        })
        assert resp.status_code == 200 or resp.status_code == 400  # 400 if already registered
        # Login
        resp = await ac.post("/auth/login", data={
            "username": "integration@example.com",
            "password": "TestPassword1!"
        })
        assert resp.status_code == 200
        tokens = resp.json()
        assert "access_token" in tokens and "refresh_token" in tokens
        access_token = tokens["access_token"]
        refresh_token = tokens["refresh_token"]
        # Get profile
        resp = await ac.get("/auth/me", headers={"Authorization": f"Bearer {access_token}"})
        assert resp.status_code == 200
        profile = resp.json()
        assert profile["email"] == "integration@example.com"
        # Refresh token
        resp = await ac.post("/auth/refresh", json={"refresh_token": refresh_token})
        assert resp.status_code == 200
        new_tokens = resp.json()
        assert "access_token" in new_tokens and "refresh_token" in new_tokens
        # Logout
        resp = await ac.post("/auth/logout", json={"refresh_token": refresh_token}, headers={"Authorization": f"Bearer {access_token}"})
        assert resp.status_code == 200
        assert resp.json()["success"] is True

@pytest.mark.asyncio
async def test_register_validation(monkeypatch):
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Invalid password (no uppercase)
        resp = await ac.post("/auth/register", json={
            "email": "badpass@example.com",
            "password": "testpassword1!",
            "full_name": "Bad Pass"
        })
        assert resp.status_code == 422
        # Invalid email
        resp = await ac.post("/auth/register", json={
            "email": "notanemail",
            "password": "TestPassword1!",
            "full_name": "Bad Email"
        })
        assert resp.status_code == 422 