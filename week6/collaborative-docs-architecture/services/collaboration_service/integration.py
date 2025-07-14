import os
import httpx
from typing import Any, Optional

DOCUMENT_SERVICE_URL = os.getenv("DOCUMENT_SERVICE_URL", "http://document_service:8000")

async def fetch_document(doc_id: str, token: str) -> Optional[Any]:
    url = f"{DOCUMENT_SERVICE_URL}/documents/{doc_id}"
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers=headers)
        if resp.status_code == 200:
            return resp.json()
        return None

async def save_document(doc_id: str, content: str, version: int, token: str) -> bool:
    url = f"{DOCUMENT_SERVICE_URL}/documents/{doc_id}"
    headers = {"Authorization": f"Bearer {token}"}
    data = {"content": content}
    async with httpx.AsyncClient() as client:
        resp = await client.put(url, json=data, headers=headers)
        return resp.status_code == 200 