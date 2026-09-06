"""In-memory sliding-window rate limiting architecture."""

import asyncio
import time
from collections import defaultdict, deque

from fastapi import Request

from app.common.exceptions.app_exceptions import RateLimitedException
from app.common.exceptions.error_codes import ErrorCode
from app.common.utils.request_utils import get_client_ip
from app.core.config import get_settings


class InMemoryRateLimiter:
    """Thread-safe in-memory sliding window rate limiter."""

    def __init__(self) -> None:
        self._records: dict[str, deque[float]] = defaultdict(deque)
        self._lock = asyncio.Lock()

    async def is_rate_limited(
        self, key: str, max_requests: int, window_seconds: int
    ) -> tuple[bool, int]:
        """Check if key exceeded limit. Returns (is_limited, retry_after_seconds)."""
        now = time.monotonic()
        async with self._lock:
            timestamps = self._records[key]
            # Remove expired timestamps
            cutoff = now - window_seconds
            while timestamps and timestamps[0] <= cutoff:
                timestamps.popleft()

            if len(timestamps) >= max_requests:
                earliest = timestamps[0]
                retry_after = max(1, int(window_seconds - (now - earliest)))
                return True, retry_after

            timestamps.append(now)
            return False, 0

    async def reset(self) -> None:
        """Clear all stored rate limit history."""
        async with self._lock:
            self._records.clear()


limiter = InMemoryRateLimiter()


class RateLimiter:
    """FastAPI dependency for rate limiting sensitive endpoints."""

    def __init__(self, times: int = 5, seconds: int = 60, action: str = "default") -> None:
        self.times = times
        self.seconds = seconds
        self.action = action

    async def __call__(self, request: Request) -> None:
        settings = get_settings()
        trusted_proxies = getattr(settings, "trusted_proxies", None)
        ip = get_client_ip(request, trusted_proxies)
        key = f"{self.action}:{ip}"

        is_limited, retry_after = await limiter.is_rate_limited(
            key=key, max_requests=self.times, window_seconds=self.seconds
        )
        if is_limited:
            raise RateLimitedException(
                message=f"Too many requests for {self.action}. Please try again in {retry_after} seconds.",
                code=ErrorCode.AUTH_RATE_LIMITED,
                details={"retry_after_seconds": retry_after, "action": self.action},
            )
