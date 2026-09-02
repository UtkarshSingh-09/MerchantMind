"""Exhaustive test suite for sliding-window Rate Limiter."""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi import HTTPException
from app.middleware.rate_limiter import check_rate_limit, _IN_MEMORY_RATE_LIMITS


@pytest.fixture(autouse=True)
def clear_in_memory_limits():
    _IN_MEMORY_RATE_LIMITS.clear()
    yield
    _IN_MEMORY_RATE_LIMITS.clear()


@pytest.mark.asyncio
async def test_rate_limiter_distinct_ip_isolation():
    """Client A reaching limit does not block Client B from same endpoint."""
    req_a = MagicMock()
    req_a.headers = {"x-forwarded-for": "192.168.1.100"}
    req_a.client.host = "192.168.1.100"

    req_b = MagicMock()
    req_b.headers = {"x-forwarded-for": "192.168.1.200"}
    req_b.client.host = "192.168.1.200"

    # Bypass Redis to test in-memory logic
    with patch("redis.asyncio.from_url", side_effect=Exception("Redis offline")):
        # Exhaust quota for Client A (max 2)
        await check_rate_limit(req_a, max_requests=2, window_seconds=60, scope="chat")
        await check_rate_limit(req_a, max_requests=2, window_seconds=60, scope="chat")

        # 3rd request from Client A blocked
        with pytest.raises(HTTPException) as exc_a:
            await check_rate_limit(req_a, max_requests=2, window_seconds=60, scope="chat")
        assert exc_a.value.status_code == 429

        # Request from Client B succeeds
        await check_rate_limit(req_b, max_requests=2, window_seconds=60, scope="chat")


@pytest.mark.asyncio
async def test_rate_limiter_scope_isolation():
    """Exhausting chat scope quota does not block checkout scope quota for same IP."""
    req = MagicMock()
    req.headers = {"x-forwarded-for": "10.0.0.1"}
    req.client.host = "10.0.0.1"

    with patch("redis.asyncio.from_url", side_effect=Exception("Redis offline")):
        # Exhaust quota for scope 'chat'
        await check_rate_limit(req, max_requests=1, window_seconds=60, scope="chat")
        with pytest.raises(HTTPException):
            await check_rate_limit(req, max_requests=1, window_seconds=60, scope="chat")

        # Scope 'orders' is still open
        await check_rate_limit(req, max_requests=5, window_seconds=60, scope="orders")


@pytest.mark.asyncio
async def test_rate_limiter_retry_after_header_present():
    """429 response includes Retry-After header with window duration."""
    req = MagicMock()
    req.headers = {}
    req.client.host = "127.0.0.1"

    with patch("redis.asyncio.from_url", side_effect=Exception("Redis offline")):
        await check_rate_limit(req, max_requests=1, window_seconds=45, scope="test")
        with pytest.raises(HTTPException) as exc:
            await check_rate_limit(req, max_requests=1, window_seconds=45, scope="test")

        assert exc.value.status_code == 429
        assert exc.value.headers.get("Retry-After") == "45"


@pytest.mark.asyncio
async def test_rate_limiter_forwarded_for_multi_hop_proxy_parsing():
    """Extracts first client IP from comma-separated X-Forwarded-For header."""
    req = MagicMock()
    req.headers = {"x-forwarded-for": "203.0.113.195, 70.41.3.18, 150.172.238.178"}
    req.client.host = "150.172.238.178"

    with patch("redis.asyncio.from_url", side_effect=Exception("Redis offline")):
        await check_rate_limit(req, max_requests=5, window_seconds=60, scope="test_proxy")
        key = "rate_limit:test_proxy:203.0.113.195"
        assert key in _IN_MEMORY_RATE_LIMITS
        assert len(_IN_MEMORY_RATE_LIMITS[key]) == 1


@pytest.mark.asyncio
async def test_rate_limiter_sliding_window_expiration():
    """Expired timestamps older than window are pruned."""
    req = MagicMock()
    req.headers = {}
    req.client.host = "1.2.3.4"
    key = "rate_limit:prune_test:1.2.3.4"

    # Inject timestamp from 70 seconds ago
    _IN_MEMORY_RATE_LIMITS[key] = [1000.0]  # Very old timestamp

    with patch("redis.asyncio.from_url", side_effect=Exception("Redis offline")):
        await check_rate_limit(req, max_requests=1, window_seconds=60, scope="prune_test")
        # Old timestamp pruned, new request permitted
        assert len(_IN_MEMORY_RATE_LIMITS[key]) == 1
