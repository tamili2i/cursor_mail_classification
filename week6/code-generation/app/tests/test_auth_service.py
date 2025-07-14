import pytest
from app.auth_service import authenticate_user, get_password_hash

class DummyUser:
    def __init__(self, email, password):
        self.email = email
        self.hashed_password = get_password_hash(password)

@pytest.mark.asyncio
async def test_authenticate_user_success(monkeypatch):
    dummy = DummyUser("test@example.com", "secret")
    async def get_user(email): return dummy if email == dummy.email else None
    result = await authenticate_user("test@example.com", "secret", get_user)
    assert result["success"] and result["user"].email == "test@example.com"

@pytest.mark.asyncio
async def test_authenticate_user_bad_password(monkeypatch):
    dummy = DummyUser("test@example.com", "secret")
    async def get_user(email): return dummy if email == dummy.email else None
    result = await authenticate_user("test@example.com", "wrong", get_user)
    assert not result["success"] and "Invalid credentials" in result["error"]

@pytest.mark.asyncio
async def test_authenticate_user_rate_limit(monkeypatch):
    dummy = DummyUser("test@example.com", "secret")
    async def get_user(email): return dummy if email == dummy.email else None
    # Simulate rate limit exceeded
    monkeypatch.setattr("app.auth_service.is_rate_limited", lambda email: True)
    result = await authenticate_user("test@example.com", "secret", get_user)
    assert not result["success"] and "Too many login attempts" in result["error"]