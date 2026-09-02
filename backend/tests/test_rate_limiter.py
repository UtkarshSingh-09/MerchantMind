"""Test suite for sliding-window token-bucket Rate Limiter."""

import pytest
from unittest.mock import MagicMock
from fastapi import HTTPException, status
from app.middleware.rate_limiter import check_rate_limit, _IN_MEMORY_RATE_LIMITS


@pytest.mark.asyncio
async def test_rate_limiter_allows_under_threshold():
    """Requests under maximum threshold are permitted."""
    mock_request = MagicMock()
    mock_request.headers = {}
    mock_request.client.host = "192.168.1.100"

    # Reset in-memory rate limits for clean test
    _IN_MEMORY_RATE_LIMITS.clear()

    for _ in range(5):
        # Should not raise exception for 5 requests when max is 10
        await check_rate_limit(mock_request, max_requests=10, window_seconds=60, scope="test_under")


@pytest.mark.asyncio
async def test_rate_limiter_blocks_over_threshold():
    """Requests exceeding maximum threshold raise 429 Too Many Requests."""
    mock_request = MagicMock()
    mock_request.headers = {}
    mock_request.client.host = "192.168.1.101"

    _IN_MEMORY_RATE_LIMITS.clear()

    # Fill quota up to limit
    for _ in range(3):
        await check_rate_limit(mock_request, max_requests=3, window_seconds=60, scope="test_over")

    # 4th request must be blocked
    with pytest.raises(HTTPException) as exc_info:
        await check_rate_limit(mock_request, max_requests=3, window_seconds=60, scope="test_over")

    assert exc_info.value.status_code == status.HTTP_429_TOO_MANY_REQUESTS
    assert "Rate limit exceeded" in exc_info.value.detail
    assert "Retry-After" in exc_info.value.headers
