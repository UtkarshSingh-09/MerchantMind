"""Circuit Breaker & Fallback Service.
Protects conversational shopping flows against LLM inference timeouts or gateway network stalls.
Provides automatic 3.5s timeout bounding and graceful fallback to deterministic rule engine.
"""

import asyncio
import logging
import time
from typing import Any, Callable, Coroutine

logger = logging.getLogger(__name__)


class CircuitBreakerOpenError(Exception):
    """Raised when the circuit breaker is open due to consecutive failures."""
    pass


class CircuitBreaker:
    """Async circuit breaker with timeout bounding and consecutive failure tracking."""

    def __init__(self, failure_threshold: int = 3, recovery_timeout_s: float = 30.0, default_timeout_s: float = 3.5):
        self.failure_threshold = failure_threshold
        self.recovery_timeout_s = recovery_timeout_s
        self.default_timeout_s = default_timeout_s
        self.failure_count = 0
        self.last_failure_time = 0.0
        self.is_open = False

    async def call_with_fallback(
        self,
        coro_fn: Callable[[], Coroutine[Any, Any, Any]],
        fallback_fn: Callable[[], Any],
        timeout_s: float | None = None,
    ) -> Any:
        """Execute async coroutine with strict timeout and fallback execution."""
        effective_timeout = timeout_s or self.default_timeout_s

        # 1. Check if circuit breaker is currently open
        if self.is_open:
            if time.time() - self.last_failure_time > self.recovery_timeout_s:
                logger.info("CircuitBreaker: Half-open state entered, attempting probe request")
                self.is_open = False
                self.failure_count = 0
            else:
                logger.warning("CircuitBreaker: Circuit is OPEN, directly invoking deterministic fallback")
                return fallback_fn() if callable(fallback_fn) else fallback_fn

        # 2. Attempt execution under strict timeout
        try:
            res = await asyncio.wait_for(coro_fn(), timeout=effective_timeout)
            # Success: reset failure count
            self.failure_count = 0
            return res
        except (asyncio.TimeoutError, Exception) as exc:
            self.failure_count += 1
            self.last_failure_time = time.time()
            if self.failure_count >= self.failure_threshold:
                self.is_open = True
                logger.error("CircuitBreaker: Threshold %d reached! Circuit is now OPEN: %s", self.failure_threshold, exc)
            else:
                logger.warning("CircuitBreaker: Call failed (%s). Failure count: %d/%d", exc, self.failure_count, self.failure_threshold)

            return fallback_fn() if callable(fallback_fn) else fallback_fn


circuit_breaker = CircuitBreaker()
