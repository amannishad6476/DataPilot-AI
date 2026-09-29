import time
from collections import defaultdict
from typing import Dict, List
from fastapi import Request
from app.core.errors import RateLimitExceededError


class InMemoryRateLimiter:
    """
    Sliding window rate limiter per client IP / tenant ID.
    Enforces resource controls to protect the API from runaway scripts or denial of service.
    """

    def __init__(self):
        # key -> list of request timestamps
        self._requests: Dict[str, List[float]] = defaultdict(list)

    def check(self, key: str, max_requests: int = 120, window_sec: int = 60) -> None:
        now = time.time()
        cutoff = now - window_sec

        # Prune old timestamps
        timestamps = [ts for ts in self._requests[key] if ts > cutoff]
        self._requests[key] = timestamps

        if len(timestamps) >= max_requests:
            retry_after = int(window_sec - (now - timestamps[0])) + 1
            raise RateLimitExceededError(
                message=f"Rate limit exceeded: max {max_requests} requests per {window_sec}s. Try again in {retry_after}s.",
                retry_after_sec=retry_after
            )

        self._requests[key].append(now)

    def reset(self):
        self._requests.clear()


limiter = InMemoryRateLimiter()


def rate_limit(max_requests: int = 120, window_sec: int = 60):
    """FastAPI dependency for endpoint rate limiting."""
    def dependency(request: Request):
        client_ip = request.client.host if request.client else "127.0.0.1"
        tenant_id = request.headers.get("X-Tenant-ID", "default")
        key = f"{tenant_id}:{client_ip}:{request.url.path}"
        limiter.check(key, max_requests=max_requests, window_sec=window_sec)
    return dependency
