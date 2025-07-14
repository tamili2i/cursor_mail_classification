from fastapi.testclient import TestClient
from app.main import app
import pytest

client = TestClient(app)

def test_register_and_read_user():
    response = client.post("/users/", json={"email": "test@example.com", "password": "secret"})
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"

    user_id = data["id"]
    response = client.get(f"/users/{user_id}")
    assert response.status_code == 200
    assert response.json()["email"] == "test@example.com"

def test_login_and_jwt_session():
    # Register user
    client.post("/users/", json={"email": "loginuser@example.com", "password": "secret"})
    # Login
    response = client.post("/users/login", data={"username": "loginuser@example.com", "password": "secret"})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    token = data["access_token"]
    # Access protected endpoint
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/users/1", headers=headers)
    assert response.status_code in (200, 404)  # User id may not be 1 if DB is not reset

def test_invalid_login():
    response = client.post("/users/login", data={"username": "nouser@example.com", "password": "wrong"})
    assert response.status_code == 400
    assert response.json()["detail"] == "Incorrect username or password"

def test_session_expiry_or_invalid():
    # Register and login
    client.post("/users/", json={"email": "expireuser@example.com", "password": "secret"})
    response = client.post("/users/login", data={"username": "expireuser@example.com", "password": "secret"})
    token = response.json()["access_token"]
    # Manually delete session in Redis (simulate logout)
    client.post("/users/logout", headers={"Authorization": f"Bearer {token}"})
    # Try to access protected endpoint
    response = client.get("/users/1", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Session expired or invalid"

def test_logout():
    # Register and login
    client.post("/users/", json={"email": "logoutuser@example.com", "password": "secret"})
    response = client.post("/users/login", data={"username": "logoutuser@example.com", "password": "secret"})
    token = response.json()["access_token"]
    # Logout
    response = client.post("/users/logout", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["msg"] == "Logged out"
    # Try to logout again (should still succeed or return 401)
    response = client.post("/users/logout", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code in (200, 401)