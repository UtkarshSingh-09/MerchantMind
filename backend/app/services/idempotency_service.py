"""Idempotency Service — Prevents double-creation of orders and payment links."""

import hashlib
import json
import logging
import uuid
from typing import Any
from app.config import settings

logger = logging.getLogger(__name__)

# In-memory LRU fallback cache for idempotency records
_IN_MEMORY_IDEMPOTENCY_CACHE: dict[str, dict[str, Any]] = {}


class IdempotencyService:
    """Provides deterministic idempotency keys and request deduplication."""

    @staticmethod
    def generate_checkout_key(
        conversation_id: uuid.UUID | str,
        merchant_id: uuid.UUID | str,
        items: list[dict[str, Any]],
        total: float | int,
    ) -> str:
        """Generate a deterministic 24-hour idempotency key based on cart payload using exact integer paise."""
        # Convert total and item prices to integer paise (1 INR = 100 paise) to eliminate float representation drift
        total_paise = int(round(float(total) * 100))
        sorted_items = sorted(
            [
                f"{str(i.get('product_id'))}:{int(i.get('quantity', 1))}:{int(round(float(i.get('price', 0) or i.get('unit_price', 0)) * 100))}"
                for i in items
            ]
        )
        raw_payload = f"{str(conversation_id)}:{str(merchant_id)}:{json.dumps(sorted_items)}:{total_paise}"
        hashed = hashlib.sha256(raw_payload.encode()).hexdigest()[:24]
        return f"idemp_ord_{hashed}"

    @staticmethod
    async def get_cached_response(key: str) -> dict[str, Any] | None:
        """Retrieve cached response if this idempotency key was previously processed."""
        # 1. Try Redis
        try:
            import redis.asyncio as aioredis
            redis_client = aioredis.from_url(settings.resolved_redis_url, decode_responses=True)
            cached_data = await redis_client.get(f"idempotency:{key}")
            await redis_client.aclose()
            if cached_data:
                logger.info("Idempotency HIT (Redis) for key: %s", key)
                return json.loads(cached_data)
        except Exception as err:
            logger.debug("Redis lookup skipped for idempotency key %s: %s", key, err)

        # 2. In-memory fallback
        if key in _IN_MEMORY_IDEMPOTENCY_CACHE:
            logger.info("Idempotency HIT (Memory) for key: %s", key)
            return _IN_MEMORY_IDEMPOTENCY_CACHE[key]

        return None

    @staticmethod
    async def record_response(key: str, response_data: dict[str, Any], ttl_seconds: int = 86400) -> None:
        """Save idempotency key and response for 24 hours."""
        _IN_MEMORY_IDEMPOTENCY_CACHE[key] = response_data

        try:
            import redis.asyncio as aioredis
            redis_client = aioredis.from_url(settings.resolved_redis_url, decode_responses=True)
            await redis_client.set(f"idempotency:{key}", json.dumps(response_data), ex=ttl_seconds)
            await redis_client.aclose()
            logger.info("Recorded idempotency key in Redis: %s", key)
        except Exception as err:
            logger.debug("Redis store skipped for idempotency key %s: %s", key, err)


idempotency_service = IdempotencyService()
