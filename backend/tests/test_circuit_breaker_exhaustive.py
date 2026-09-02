"""Exhaustive state-machine test suite for CircuitBreaker."""

import asyncio
import time
import pytest
from app.services.circuit_breaker import CircuitBreaker


@pytest.mark.asyncio
async def test_cb_normal_execution_success():
    """Successful function calls return result directly and keep failure count at 0."""
    cb = CircuitBreaker(failure_threshold=3, recovery_timeout_s=5.0)

    async def successful_fn():
        return "SUCCESS_DATA"

    res = await cb.call_with_fallback(successful_fn, lambda: "FALLBACK_DATA")
    assert res == "SUCCESS_DATA"
    assert cb.failure_count == 0
    assert cb.is_open is False


@pytest.mark.asyncio
async def test_cb_single_failure_increments_count_returns_fallback():
    """Single failure invokes fallback and increments failure count without opening circuit."""
    cb = CircuitBreaker(failure_threshold=3, recovery_timeout_s=5.0)

    async def failing_fn():
        raise RuntimeError("Transient network blip")

    res = await cb.call_with_fallback(failing_fn, lambda: "SAFE_FALLBACK")
    assert res == "SAFE_FALLBACK"
    assert cb.failure_count == 1
    assert cb.is_open is False


@pytest.mark.asyncio
async def test_cb_timeout_triggers_fallback():
    """Async task exceeding timeout threshold invokes fallback."""
    cb = CircuitBreaker(failure_threshold=3, default_timeout_s=0.05)

    async def slow_fn():
        await asyncio.sleep(0.5)
        return "SLOW_DATA"

    res = await cb.call_with_fallback(slow_fn, lambda: "TIMEOUT_FALLBACK")
    assert res == "TIMEOUT_FALLBACK"
    assert cb.failure_count == 1


@pytest.mark.asyncio
async def test_cb_trips_to_open_after_reaching_threshold():
    """Circuit transitions to OPEN after 3 consecutive failures."""
    cb = CircuitBreaker(failure_threshold=3, recovery_timeout_s=10.0)

    async def failing_fn():
        raise ValueError("Service down")

    for _ in range(3):
        await cb.call_with_fallback(failing_fn, lambda: "FALLBACK")

    assert cb.failure_count == 3
    assert cb.is_open is True


@pytest.mark.asyncio
async def test_cb_open_state_short_circuits_without_calling_fn():
    """When circuit is OPEN, primary function is not called at all."""
    cb = CircuitBreaker(failure_threshold=2, recovery_timeout_s=10.0)
    cb.is_open = True
    cb.last_failure_time = time.time()

    called = False

    async def should_not_run():
        nonlocal called
        called = True
        return "DATA"

    res = await cb.call_with_fallback(should_not_run, lambda: "DIRECT_FALLBACK")
    assert res == "DIRECT_FALLBACK"
    assert called is False  # Proves function was bypassed entirely


@pytest.mark.asyncio
async def test_cb_half_open_recovery_probe():
    """After recovery timeout expires, circuit attempts probe and resets on success."""
    cb = CircuitBreaker(failure_threshold=2, recovery_timeout_s=0.1)
    cb.is_open = True
    cb.last_failure_time = time.time() - 0.2  # Past recovery timeout

    async def recovered_fn():
        return "RECOVERED_DATA"

    res = await cb.call_with_fallback(recovered_fn, lambda: "FALLBACK")
    assert res == "RECOVERED_DATA"
    assert cb.is_open is False
    assert cb.failure_count == 0
