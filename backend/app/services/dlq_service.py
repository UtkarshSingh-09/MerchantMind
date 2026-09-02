"""Dead Letter Queue (DLQ) Service — Stores and retries failed webhooks with exponential backoff."""

import logging
from typing import Any
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.dead_letter import WebhookDeadLetter

logger = logging.getLogger(__name__)


class DLQService:
    """Manages recording and replaying dead-letter webhook events."""

    @staticmethod
    async def record_dead_letter(
        db: AsyncSession,
        event_type: str,
        payload: dict[str, Any],
        error_message: str,
        source: str = "razorpay",
        event_id: str | None = None,
    ) -> WebhookDeadLetter:
        """Store a failed webhook in the DLQ table."""
        dlq_entry = WebhookDeadLetter(
            event_id=event_id,
            event_type=event_type,
            source=source,
            payload=payload,
            error_message=error_message,
            retry_count=0,
            status="pending",
        )
        db.add(dlq_entry)
        try:
            await db.flush()
            logger.warning("Recorded failed %s webhook into DLQ: event_type=%s, error=%s", source, event_type, error_message)
        except Exception as e:
            logger.error("Failed to write to DLQ table: %s", e)
        return dlq_entry

    @staticmethod
    async def get_pending_dead_letters(db: AsyncSession, limit: int = 20) -> list[WebhookDeadLetter]:
        """Fetch pending dead letters for reconciliation retry."""
        stmt = (
            select(WebhookDeadLetter)
            .where(WebhookDeadLetter.status.in_(["pending", "retried"]))
            .where(WebhookDeadLetter.retry_count < 5)
            .order_by(WebhookDeadLetter.created_at.desc())
            .limit(limit)
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())


dlq_service = DLQService()
