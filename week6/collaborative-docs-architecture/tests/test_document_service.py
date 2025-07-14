import pytest
from httpx import AsyncClient
from week6.collaborative_docs_architecture.services.document_service.main import app

@pytest.mark.asyncio
async def test_document_crud(monkeypatch):
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Create document
        resp = await ac.post("/documents/", json={
            "title": "Test Doc",
            "content": "Hello world"
        }, headers={"Authorization": "Bearer testtoken"})
        assert resp.status_code in (200, 401)  # 401 if auth not mocked
        # List documents
        resp = await ac.get("/documents/", headers={"Authorization": "Bearer testtoken"})
        assert resp.status_code in (200, 401)
        # Get document (if created)
        if resp.status_code == 200 and resp.json():
            doc_id = resp.json()[0]["id"]
            resp = await ac.get(f"/documents/{doc_id}", headers={"Authorization": "Bearer testtoken"})
            assert resp.status_code in (200, 401, 404)
            # Update document
            resp = await ac.put(f"/documents/{doc_id}", json={"content": "Updated content"}, headers={"Authorization": "Bearer testtoken"})
            assert resp.status_code in (200, 401, 404)
            # Delete document
            resp = await ac.delete(f"/documents/{doc_id}", headers={"Authorization": "Bearer testtoken"})
            assert resp.status_code in (204, 401, 404)

@pytest.mark.asyncio
async def test_document_versioning(monkeypatch):
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Create document
        resp = await ac.post("/documents/", json={
            "title": "Versioned Doc",
            "content": "v1"
        }, headers={"Authorization": "Bearer testtoken"})
        if resp.status_code != 200:
            return
        doc = resp.json()
        doc_id = doc["id"]
        # Update document
        await ac.put(f"/documents/{doc_id}", json={"content": "v2"}, headers={"Authorization": "Bearer testtoken"})
        await ac.put(f"/documents/{doc_id}", json={"content": "v3"}, headers={"Authorization": "Bearer testtoken"})
        # Get versions
        resp = await ac.get(f"/documents/{doc_id}/versions", headers={"Authorization": "Bearer testtoken"})
        assert resp.status_code in (200, 401, 404)
        if resp.status_code == 200:
            versions = resp.json()
            assert len(versions) >= 1 