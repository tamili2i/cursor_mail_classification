import os
import redis
import json

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
REDIS_URL = os.getenv("REDIS_URL", f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}")

_redis = None

def get_redis():
    global _redis
    if _redis is None:
        _redis = redis.Redis.from_url(REDIS_URL, decode_responses=True)
    return _redis

def redis_set(key, value, ex=None):
    r = get_redis()
    if isinstance(value, (dict, list)):
        value = json.dumps(value)
    return r.set(key, value, ex=ex)

def redis_get(key):
    r = get_redis()
    val = r.get(key)
    try:
        return json.loads(val)
    except Exception:
        return val

def redis_delete(key):
    r = get_redis()
    return r.delete(key) 