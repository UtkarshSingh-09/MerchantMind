"""Conversation and Cart persistence service."""

import uuid
from datetime import datetime, timezone
from typing import Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.conversation import Conversation
from app.models.merchant import Merchant


async def get_or_create_conversation(
    db: AsyncSession,
    merchant_id: uuid.UUID | None = None,
    conversation_id: uuid.UUID | None = None,
    channel: str = "web",
    customer_phone: str | None = None,
    customer_id: uuid.UUID | None = None,
) -> Conversation:
    """Fetch existing conversation or create a new one.

    If merchant_id is None, creates a Discovery Mode conversation.
    """
    if conversation_id:
        stmt = select(Conversation).where(Conversation.id == conversation_id)
        result = await db.execute(stmt)
        conv = result.scalar_one_or_none()
        if conv:
            if merchant_id and conv.merchant_id != merchant_id:
                conv.merchant_id = merchant_id
            if customer_id and not conv.customer_id:
                conv.customer_id = customer_id
            return conv

    # Verify merchant exists (if provided)
    if merchant_id:
        stmt_m = select(Merchant).where(Merchant.id == merchant_id)
        res_m = await db.execute(stmt_m)
        merchant = res_m.scalar_one_or_none()
        if not merchant:
            raise ValueError(f"Merchant {merchant_id} not found")

    new_conv = Conversation(
        id=conversation_id or uuid.uuid4(),
        merchant_id=merchant_id,  # None for Discovery Mode
        customer_id=customer_id,
        channel=channel,
        messages=[],
        cart={"items": [], "total": 0.0},
        agent_reasoning=[],
        handoff_context={},
        status="active",
    )
    db.add(new_conv)
    await db.flush()
    await db.refresh(new_conv)
    return new_conv


async def lock_conversation_to_merchant(
    db: AsyncSession,
    conversation: Conversation,
    merchant_id: uuid.UUID,
    handoff_data: dict[str, Any] | None = None,
) -> Conversation:
    """Lock a discovery conversation to a specific merchant once user picks one.

    This transitions the conversation from Discovery Mode to Shopping Mode.
    """
    stmt = select(Merchant).where(Merchant.id == merchant_id)
    res = await db.execute(stmt)
    merchant = res.scalar_one_or_none()
    if not merchant:
        raise ValueError(f"Merchant {merchant_id} not found")

    conversation.merchant_id = merchant_id
    if handoff_data:
        conversation.handoff_context = handoff_data
    return conversation


async def get_conversation_by_id(
    db: AsyncSession,
    conversation_id: uuid.UUID,
) -> Conversation | None:
    """Fetch conversation by ID."""
    stmt = select(Conversation).where(Conversation.id == conversation_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


def add_message_to_conversation(
    conversation: Conversation,
    role: str,
    content: str,
    metadata: dict[str, Any] | None = None,
) -> None:
    """Append a message to the conversation JSONB messages array."""
    messages = list(conversation.messages or [])
    msg_entry = {
        "role": role,
        "content": content,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "metadata": metadata or {},
    }
    messages.append(msg_entry)
    conversation.messages = messages


def update_conversation_cart(
    conversation: Conversation,
    cart_data: dict[str, Any],
) -> None:
    """Update cart JSONB structure and recalculate total."""
    items = cart_data.get("items", [])
    total = sum(item.get("price", 0.0) * item.get("quantity", 1) for item in items)
    conversation.cart = {
        "items": items,
        "total": round(total, 2),
    }


def add_agent_reasoning(
    conversation: Conversation,
    action: str,
    reasoning: str,
    data: dict[str, Any] | None = None,
) -> None:
    """Track agent decision & reasoning for auditability."""
    reasonings = list(conversation.agent_reasoning or [])
    reasonings.append(
        {
            "action": action,
            "reasoning": reasoning,
            "data": data or {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )
    conversation.agent_reasoning = reasonings


def set_handoff_context(
    conversation: Conversation,
    handoff_data: dict[str, Any],
) -> None:
    """Store agent handoff context."""
    existing = dict(conversation.handoff_context or {})
    existing.update(handoff_data)
    conversation.handoff_context = existing

