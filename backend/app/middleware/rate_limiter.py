"""Sliding-window token-bucket Rate Limiter middleware.
Protects AI endpoints and payment checkout routes against high-frequency abuse and token exhaustion.
"""

import time
import logging
from typing import Callable
from fastapi import Request, HTTPException, status
from app.config import settings

logger = logging.getLogger(__name__)

# Fallback in-memory store if Redis is unreachable: {key: [(timestamp)]}
_IN_MEMORY_RATE_LIMITS: dict[str, list[float]] = {}


async def check_rate_limit(
    request: Request,
    max_requests: int = 60,
    window_seconds: int = 60,
    scope: str = "default",
):
    """Check if the requesting client has exceeded the sliding-window rate limit.
    
    Identifies clients by X-Forwarded-For, client IP, or Authorization/Session tokens.
    """
    client_ip = (
        request.headers.get("x-forwarded-for", "").split(",")[0].strip()
        or (request.client.host if request.client else "unknown_ip")
    )
    key = f"rate_limit:{scope}:{client_ip}"
    now = time.time()

    # 1. Try distributed Redis rate limiting
    try:
        import redis.asyncio as aioredis
        redis_client = aioredis.from_url(settings.resolved_redis_url, decode_responses=True)
        current = await redis_client.incr(key)
        if current == 1:
            await redis_client.expire(key, window_seconds)
        await redis_client.aclose()

        if current > max_requests:
            logger.warning("Rate limit exceeded for client %s in scope '%s': %d/%d", client_ip, scope, current, max_requests)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Maximum {max_requests} requests per {window_seconds}s allowed.",
                headers={"Retry-After": str(window_seconds)},
            )
        return
    except HTTPException:
        raise
    except Exception:
        pass

    # 2. In-Memory fallback sliding-window
    timestamps = _IN_MEMORY_RATE_LIMITS.setdefault(key, [])
    cutoff = now - window_seconds
    # Prune expired timestamps
    _IN_MEMORY_RATE_LIMITS[key] = [t for t in timestamps if t > cutoff]
    
    if len(_IN_MEMORY_RATE_LIMITS[key]) >= max_requests:
        logger.warning("In-memory rate limit exceeded for client %s in scope '%s'", client_ip, scope)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Maximum {max_requests} requests per {window_seconds}s allowed.",
            headers={"Retry-After": str(window_seconds)},
        )

    _IN_MEMORY_RATE_LIMITS[key].append(now)


def rate_limit(max_requests: int = 60, window_seconds: int = 60, scope: str = "default") -> Callable:
    """FastAPI Dependency for route-level rate limiting."""
    async def dependency(request: Request):
        await check_rate_limit(
            request=request,
            max_requests=max_requests,
            window_seconds=window_seconds,
            scope=scope,
        )
    return dependency
