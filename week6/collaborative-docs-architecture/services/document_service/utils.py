import os
import aioredis
import json
from typing import Optional, Any

_redis = None

async def get_redis():
    global _redis
    if not _redis:
        _redis = await aioredis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"), decode_responses=True)
    return _redis

async def cache_document(doc_id: str, doc: Any, expire: int = 300):
    redis = await get_redis()
    await redis.set(f"doc:{doc_id}", json.dumps(doc), ex=expire)

async def get_cached_document(doc_id: str) -> Optional[Any]:
    redis = await get_redis()
    data = await redis.get(f"doc:{doc_id}")
    if data:
        return json.loads(data)
    return None

async def cache_search_results(user_id: str, query: str, results: Any, expire: int = 120):
    redis = await get_redis()
    key = f"search:{user_id}:{query}"
    await redis.set(key, json.dumps(results), ex=expire)

async def get_cached_search_results(user_id: str, query: str) -> Optional[Any]:
    redis = await get_redis()
    key = f"search:{user_id}:{query}"
    data = await redis.get(key)
    if data:
        return json.loads(data)
    return None 