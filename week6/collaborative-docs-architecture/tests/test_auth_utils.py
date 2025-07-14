import pytest
import asyncio
from datetime import timedelta
from unittest.mock import AsyncMock, patch
from week6.collaborative_docs_architecture.services.user_service.main import (
    get_password_hash, verify_password, create_access_token, create_refresh_token, decode_token,
    is_rate_limited, increment_rate_limit, reset_rate_limit, is_account_locked, lock_account, unlock_account,
    Settings
)

@pytest.mark.asyncio
async def test_password_hash_and_verify():
    password = "TestPassword1!"
    hashed = get_password_hash(password)
    assert verify_password(password, hashed)
    assert not verify_password("WrongPassword", hashed)

@pytest.mark.asyncio
async def test_jwt_token_creation_and_decode():
    data = {"sub": "user123"}
    access_token = create_access_token(data, expires_delta=timedelta(minutes=1))
    decoded = decode_token(access_token)
    assert decoded["sub"] == "user123"
    assert decoded["type"] == "access"
    refresh_token = create_refresh_token(data, expires_delta=timedelta(minutes=1))
    decoded_r = decode_token(refresh_token)
    assert decoded_r["type"] == "refresh"

@pytest.mark.asyncio
async def test_rate_limiting(monkeypatch):
    redis = AsyncMock()
    redis.get = AsyncMock(return_value=None)
    redis.pipeline.return_value = redis
    redis.incr = AsyncMock()
    redis.expire = AsyncMock()
    redis.execute = AsyncMock()
    redis.delete = AsyncMock()
    key = "rl:test:user@example.com"
    # Not rate limited initially
    assert not await is_rate_limited(redis, key)
    # Simulate rate limited
    redis.get = AsyncMock(return_value=str(Settings().RATE_LIMIT_ATTEMPTS))
    assert await is_rate_limited(redis, key)
    # Increment and reset
    await increment_rate_limit(redis, key)
    await reset_rate_limit(redis, key)
    redis.incr.assert_called_with(key)
    redis.expire.assert_called_with(key, Settings().RATE_LIMIT_WINDOW)
    redis.delete.assert_called_with(key)

@pytest.mark.asyncio
async def test_account_lockout(monkeypatch):
    redis = AsyncMock()
    email = "user@example.com"
    lock_key = f"lockout:{email}"
    redis.get = AsyncMock(return_value=None)
    assert not await is_account_locked(redis, email)
    redis.get = AsyncMock(return_value="1")
    assert await is_account_locked(redis, email)
    redis.set = AsyncMock()
    await lock_account(redis, email)
    redis.set.assert_called_with(lock_key, "1", ex=Settings().ACCOUNT_LOCKOUT_DURATION)
    redis.delete = AsyncMock()
    await unlock_account(redis, email)
    redis.delete.assert_called_with(lock_key) 