import time
import threading
from collections import defaultdict, deque
from fastapi import Request, Response
import psutil
import redis
from app.core.redis import get_redis

# --- API Performance Metrics ---
api_metrics = defaultdict(lambda: {"count": 0, "total_time": 0.0, "times": deque(maxlen=1000)})
active_users = set()
api_lock = threading.Lock()

class APIMonitoringMiddleware:
    def __init__(self, app):
        self.app = app
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            start = time.time()
            request = Request(scope, receive=receive)
            user = request.headers.get("Authorization", "anonymous")
            path = scope["path"]
            method = scope["method"]
            endpoint = f"{method} {path}"
            with api_lock:
                active_users.add(user)
            async def send_wrapper(message):
                if message["type"] == "http.response.start":
                    elapsed = time.time() - start
                    with api_lock:
                        m = api_metrics[endpoint]
                        m["count"] += 1
                        m["total_time"] += elapsed
                        m["times"].append(elapsed)
            await self.app(scope, receive, send_wrapper)
            with api_lock:
                if user != "anonymous":
                    active_users.discard(user)
        else:
            await self.app(scope, receive, send)

# --- DB Query Metrics (from slow query logger) ---
db_query_times = deque(maxlen=1000)
db_slow_query_count = 0
db_lock = threading.Lock()

def log_db_query_time(duration):
    global db_slow_query_count
    with db_lock:
        db_query_times.append(duration)
        if duration > 0.2:
            db_slow_query_count += 1

def get_db_metrics():
    with db_lock:
        count = len(db_query_times)
        avg = sum(db_query_times) / count if count else 0
        slow = db_slow_query_count
    return {"query_count": count, "avg_query_time": avg, "slow_query_count": slow}

# --- Cache Metrics (from crud) ---
def get_cache_metrics():
    from app.crud import get_cache_metrics as crud_cache_metrics
    return crud_cache_metrics()

# --- System Resource Usage ---
def get_system_metrics():
    cpu = psutil.cpu_percent(interval=0.1)
    mem = psutil.virtual_memory()
    return {
        "cpu_percent": cpu,
        "memory_percent": mem.percent,
        "memory_used_mb": mem.used // 1024 // 1024,
        "memory_total_mb": mem.total // 1024 // 1024,
    }

# --- Active User Metrics ---
def get_active_user_count():
    with api_lock:
        return len(active_users)

def get_api_metrics():
    with api_lock:
        return {
            ep: {
                "count": m["count"],
                "avg_time": m["total_time"] / m["count"] if m["count"] else 0,
                "p95_time": sorted(m["times"])[int(0.95 * len(m["times"]))] if m["times"] else 0,
            }
            for ep, m in api_metrics.items()
        }

def get_monitoring_dashboard():
    return {
        "api_metrics": get_api_metrics(),
        "active_user_count": get_active_user_count(),
        "db_metrics": get_db_metrics(),
        "cache_metrics": get_cache_metrics(),
        "system_metrics": get_system_metrics(),
    } 