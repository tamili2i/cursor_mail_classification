import pytest
from httpx import AsyncClient
from week6.collaborative_docs_architecture.services.user_service.main import app
import jwt

@pytest.mark.asyncio
async def test_sql_injection_on_login():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Attempt SQL injection in username
        resp = await ac.post("/auth/login", data={
            "username": "' OR 1=1;--",
            "password": "irrelevant"
        })
        assert resp.status_code == 401 or resp.status_code == 422

@pytest.mark.asyncio
async def test_xss_in_registration():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        resp = await ac.post("/auth/register", json={
            "email": "xss@example.com",
            "password": "TestPassword1!",
            "full_name": "<script>alert('xss')</script>"
        })
        # Should succeed, but output should not reflect raw input (no XSS in API)
        assert resp.status_code == 200 or resp.status_code == 400
        if resp.status_code == 200:
            assert "<script>" not in resp.text

@pytest.mark.asyncio
async def test_jwt_tampering():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Register and login to get a valid token
        await ac.post("/auth/register", json={
            "email": "jwt-tamper@example.com",
            "password": "TestPassword1!",
            "full_name": "JWT Tamper"
        })
        resp = await ac.post("/auth/login", data={
            "username": "jwt-tamper@example.com",
            "password": "TestPassword1!"
        })
        tokens = resp.json()
        access_token = tokens["access_token"]
        # Tamper with the token (change a char)
        tampered = access_token[:-2] + ("A" if access_token[-1] != "A" else "B")
        resp = await ac.get("/auth/me", headers={"Authorization": f"Bearer {tampered}"})
        assert resp.status_code == 401

@pytest.mark.asyncio
async def test_brute_force_protection():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        email = "brute@example.com"
        await ac.post("/auth/register", json={
            "email": email,
            "password": "TestPassword1!",
            "full_name": "Brute Force"
        })
        # Exceed login attempts
        for _ in range(15):
            resp = await ac.post("/auth/login", data={
                "username": email,
                "password": "WrongPassword!"
            })
        # Should be locked out
        resp = await ac.post("/auth/login", data={
            "username": email,
            "password": "TestPassword1!"
        })
        assert resp.status_code == 423 or resp.status_code == 429 