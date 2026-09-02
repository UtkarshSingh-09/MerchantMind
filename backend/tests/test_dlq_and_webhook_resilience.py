"""Test suite for Dead-Letter Queue (DLQ) and Webhook Ingestion Resilience."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.dlq_service import dlq_service
from app.models.dead_letter import WebhookDeadLetter


@pytest.mark.asyncio
async def test_dlq_record_failed_webhook(db_session: AsyncSession):
    """Failed webhook records complete event payload and error message into DLQ."""
    payload = {"event": "payment.captured", "payload": {"payment": {"entity": {"id": "pay_test123"}}}}
    entry = await dlq_service.record_dead_letter(
        db=db_session,
        event_type="payment.captured",
        payload=payload,
        error_message="Database connection pool timeout",
        source="razorpay",
        event_id="evt_fail_999",
    )
    await db_session.commit()

    assert entry.id is not None
    assert entry.status == "pending"
    assert entry.retry_count == 0
    assert entry.event_id == "evt_fail_999"
    assert entry.error_message == "Database connection pool timeout"


@pytest.mark.asyncio
async def test_dlq_get_pending_dead_letters_filtering(db_session: AsyncSession):
    """Pending retrieval filters out items exceeding max retry count (>= 5)."""
    # 1. Active pending item
    e1 = WebhookDeadLetter(
        event_type="payment.captured",
        source="razorpay",
        payload={"order": "1"},
        error_message="err",
        retry_count=1,
        status="pending",
    )
    # 2. Exhausted item (retry_count = 5)
    e2 = WebhookDeadLetter(
        event_type="payment.captured",
        source="razorpay",
        payload={"order": "2"},
        error_message="fatal",
        retry_count=5,
        status="retried",
    )
    # 3. Already resolved item
    e3 = WebhookDeadLetter(
        event_type="payment.captured",
        source="razorpay",
        payload={"order": "3"},
        error_message="resolved",
        retry_count=2,
        status="resolved",
    )
    db_session.add_all([e1, e2, e3])
    await db_session.commit()

    pending = await dlq_service.get_pending_dead_letters(db_session, limit=10)
    pending_ids = [str(x.id) for x in pending]

    assert str(e1.id) in pending_ids
    assert str(e2.id) not in pending_ids  # Filtered by retry_count < 5
    assert str(e3.id) not in pending_ids  # Filtered by status != resolved
