"""WhatsApp Session Manager — maps incoming WhatsApp sender to Customer and Conversation."""

import uuid
import logging
from datetime import datetime, timezone, timedelta
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.merchant import Merchant
from app.models.customer import Customer
from app.models.conversation import Conversation

logger = logging.getLogger(__name__)


async def get_default_merchant(db: AsyncSession) -> Merchant | None:
    """Fetch the default primary active merchant for incoming WhatsApp messages."""
    stmt = select(Merchant).where(Merchant.is_active == True).order_by(Merchant.created_at.asc()).limit(1)
    res = await db.execute(stmt)
    return res.scalar_one_or_none()


async def get_or_create_whatsapp_session(
    db: AsyncSession,
    customer_phone: str,
    merchant_id: uuid.UUID | None = None,
    customer_name: str | None = None,
) -> tuple[Conversation, Customer, Merchant]:
    """Resolve or create the Customer, Conversation, and Merchant for an incoming WhatsApp message."""
    # 1. Resolve merchant
    merchant = None
    if merchant_id:
        m_stmt = select(Merchant).where(Merchant.id == merchant_id)
        m_res = await db.execute(m_stmt)
        merchant = m_res.scalar_one_or_none()

    if not merchant:
        merchant = await get_default_merchant(db)

    if not merchant:
        raise ValueError("No active merchant found in system to handle WhatsApp conversation.")

    # 2. Resolve or create Customer
    clean_phone = "".join(filter(str.isdigit, customer_phone))
    cust_stmt = select(Customer).where(
        Customer.merchant_id == merchant.id,
        Customer.phone == clean_phone,
    )
    cust_res = await db.execute(cust_stmt)
    customer = cust_res.scalar_one_or_none()

    if not customer:
        customer = Customer(
            merchant_id=merchant.id,
            name=customer_name or f"WhatsApp User ({clean_phone[-4:]})",
            phone=clean_phone,
        )
        db.add(customer)
        await db.flush()
        logger.info("Created new customer %s for phone %s", customer.id, clean_phone)

    # 3. Resolve active WhatsApp Conversation (created within last 24h)
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    conv_stmt = select(Conversation).where(
        and_(
            Conversation.merchant_id == merchant.id,
            Conversation.customer_id == customer.id,
            Conversation.channel == "whatsapp",
            Conversation.status == "active",
            Conversation.updated_at >= cutoff,
        )
    ).order_by(Conversation.updated_at.desc()).limit(1)

    conv_res = await db.execute(conv_stmt)
    conversation = conv_res.scalar_one_or_none()

    if not conversation:
        conversation = Conversation(
            merchant_id=merchant.id,
            customer_id=customer.id,
            channel="whatsapp",
            status="active",
            messages=[],
            cart={"items": [], "total": 0.0},
            agent_reasoning=[],
        )
        db.add(conversation)
        await db.flush()
        logger.info("Started new WhatsApp conversation %s for customer %s", conversation.id, customer.id)

    return conversation, customer, merchant
