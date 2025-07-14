import pytest
import asyncio
import time
from httpx import AsyncClient
from week6.collaborative_docs_architecture.services.user_service.main import app

@pytest.mark.asyncio
async def test_concurrent_registration_and_login():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        users = [
            {"email": f"perfuser{i}@example.com", "password": "TestPassword1!", "full_name": f"Perf User {i}"}
            for i in range(10)
        ]
        # Register users concurrently
        start = time.time()
        reg_tasks = [ac.post("/auth/register", json=user) for user in users]
        reg_results = await asyncio.gather(*reg_tasks)
        assert all(r.status_code in (200, 400) for r in reg_results)  # 400 if already registered
        # Login users concurrently
        login_tasks = [ac.post("/auth/login", data={"username": user["email"], "password": user["password"]}) for user in users]
        login_results = await asyncio.gather(*login_tasks)
        assert all(r.status_code == 200 for r in login_results)
        elapsed = time.time() - start
        print(f"Concurrent registration and login for 10 users took {elapsed:.2f} seconds")
        assert elapsed < 10  # Should be reasonably fast 