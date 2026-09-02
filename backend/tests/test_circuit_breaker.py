"""Tests for Circuit Breaker and LLM Timeout Fallback."""

import asyncio
import pytest
from app.services.circuit_breaker import CircuitBreaker


@pytest.mark.asyncio
async def test_circuit_breaker_timeout_triggers_fallback():
    """Verify that a hanging async coroutine triggers fallback immediately upon 0.1s timeout."""
    cb = CircuitBreaker(default_timeout_s=0.1)

    async def hanging_llm_inference():
        await asyncio.sleep(1.0)
        return "slow_llm_response"

    def fast_deterministic_fallback():
        return "fallback_deterministic_response"

    result = await cb.call_with_fallback(hanging_llm_inference, fast_deterministic_fallback)
    assert result == "fallback_deterministic_response"


@pytest.mark.asyncio
async def test_circuit_breaker_opens_after_consecutive_failures():
    """Verify circuit breaker transitions to OPEN after reaching threshold."""
    cb = CircuitBreaker(failure_threshold=2, default_timeout_s=0.05)

    async def failing_call():
        raise ConnectionError("Groq endpoint unreachable")

    def fallback():
        return "fallback_triggered"

    # Call 1: failure 1
    res1 = await cb.call_with_fallback(failing_call, fallback)
    assert res1 == "fallback_triggered"
    assert cb.is_open is False

    # Call 2: failure 2 -> reaches threshold 2 -> Opens circuit
    res2 = await cb.call_with_fallback(failing_call, fallback)
    assert res2 == "fallback_triggered"
    assert cb.is_open is True

    # Call 3: Circuit is OPEN, skips call immediately
    res3 = await cb.call_with_fallback(failing_call, fallback)
    assert res3 == "fallback_triggered"
