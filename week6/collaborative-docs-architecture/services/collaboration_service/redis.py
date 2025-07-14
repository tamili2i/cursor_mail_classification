import os
import aioredis
import json
from typing import Any, Optional, List

_redis = None

async def get_redis():
    global _redis
    if not _redis:
        _redis = await aioredis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"), decode_responses=True)
    return _redis

async def publish_event(doc_id: str, event: Any):
    redis = await get_redis()
    stream = f"docstream:{doc_id}"
    await redis.xadd(stream, {"event": json.dumps(event)}, maxlen=1000)

async def consume_events(doc_id: str, last_id: str = "$", count: int = 10) -> List[Any]:
    redis = await get_redis()
    stream = f"docstream:{doc_id}"
    events = await redis.xread({stream: last_id}, count=count, block=1000)
    result = []
    for _, entries in events:
        for entry_id, data in entries:
            event = json.loads(data["event"])
            result.append((entry_id, event))
    return result 