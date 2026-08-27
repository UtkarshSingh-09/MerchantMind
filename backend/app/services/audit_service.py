"""Centralized Audit Trail Service for system-wide decision tracking and compliance."""

import uuid
import logging
from enum import Enum
from typing import Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog

logger = logging.getLogger(__name__)


class AuditEventType(str, Enum):
    AGENT_DECISION = "agent_decision"
    AGENT_FALLBACK = "agent_fallback"
    RAZORPAY_ORDER = "razorpay_order"
    RAZORPAY_PAYMENT_LINK = "razorpay_link"
    RAZORPAY_WEBHOOK = "razorpay_webhook"
    WHATSAPP_INBOUND = "whatsapp_inbound"
    WHATSAPP_OUTBOUND = "whatsapp_outbound"
    BUDGET_CHECK = "budget_check"
    BUDGET_VIOLATION = "budget_violation"
    CHECKOUT_INITIATED = "checkout_initiated"
    PAYMENT_CAPTURED = "payment_captured"
    PAYMENT_FAILED = "payment_failed"


async def log_audit_event(
    db: AsyncSession,
    event_type: AuditEventType | str,
    merchant_id: uuid.UUID,
    action: str,
    reasoning: str,
    order_id: uuid.UUID | None = None,
    conversation_id: uuid.UUID | None = None,
    input_data: dict[str, Any] | None = None,
    output_data: dict[str, Any] | None = None,
) -> AuditLog:
    """Log an immutable audit trail entry."""
    ev_type = event_type.value if isinstance(event_type, AuditEventType) else str(event_type)
    audit_entry = AuditLog(
        id=uuid.uuid4(),
        merchant_id=merchant_id,
        order_id=order_id,
        conversation_id=conversation_id,
        event_type=ev_type,
        action=action,
        reasoning=reasoning,
        input_data=input_data or {},
        output_data=output_data or {},
    )
    db.add(audit_entry)
    await db.flush()
    logger.info("AUDIT [%s] merchant=%s order=%s: %s (%s)", ev_type, merchant_id, order_id, action, reasoning[:80])
    return audit_entry


async def get_order_audit_trail(
    db: AsyncSession,
    order_id: uuid.UUID,
) -> list[AuditLog]:
    """Retrieve full chronological audit trail for a specific order."""
    stmt = select(AuditLog).where(AuditLog.order_id == order_id).order_by(AuditLog.created_at.asc())
    res = await db.execute(stmt)
    return list(res.scalars().all())


async def get_conversation_audit_trail(
    db: AsyncSession,
    conversation_id: uuid.UUID,
) -> list[AuditLog]:
    """Retrieve all audit events related to a conversation session."""
    stmt = select(AuditLog).where(AuditLog.conversation_id == conversation_id).order_by(AuditLog.created_at.asc())
    res = await db.execute(stmt)
    return list(res.scalars().all())


async def get_merchant_audit_trail(
    db: AsyncSession,
    merchant_id: uuid.UUID,
    limit: int = 100,
) -> list[AuditLog]:
    """Retrieve recent audit events for a merchant."""
    stmt = select(AuditLog).where(AuditLog.merchant_id == merchant_id).order_by(AuditLog.created_at.desc()).limit(limit)
    res = await db.execute(stmt)
    return list(res.scalars().all())
