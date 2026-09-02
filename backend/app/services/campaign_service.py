"""Campaign Orchestrator Service — identifies dormant customers, crafts personalized AI offers, and dispatches via WhatsApp."""

import uuid
import logging
from datetime import datetime, timezone, timedelta
from typing import Any
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.merchant import Merchant
from app.models.customer import Customer
from app.models.campaign import Campaign
from app.services.groq_client import groq_client
from app.services.whatsapp_service import whatsapp_service
from app.services.razorpay_service import razorpay_service

logger = logging.getLogger(__name__)


async def find_dormant_customers(
    db: AsyncSession,
    merchant_id: uuid.UUID,
    days_inactive: int = 14,
) -> list[Customer]:
    """Find customers who haven't ordered in `days_inactive` days or never ordered."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days_inactive)
    stmt = select(Customer).where(
        and_(
            Customer.merchant_id == merchant_id,
            or_(
                Customer.last_order_at.is_(None),
                Customer.last_order_at < cutoff,
            ),
        )
    ).limit(50)

    res = await db.execute(stmt)
    return list(res.scalars().all())


async def generate_personalized_reengagement(
    merchant: Merchant,
    customer: Customer,
    discount_pct: int = 15,
) -> str:
    """Use Groq LLM to generate an enticing, personalized re-engagement message."""
    prompt = f"""You are the marketing growth AI for '{merchant.name}'.
Write a warm, concise WhatsApp re-engagement message for customer '{customer.name or 'Valued Customer'}'.
Offer: Exclusive {discount_pct}% OFF on their next order!
Keep it under 3 short sentences, friendly, and include an invitation to reply directly on WhatsApp.
Do not include placeholder brackets like [Customer Name].
"""
    try:
        response = await groq_client.chat_completion(
            messages=[
                {"role": "system", "content": "You craft high-converting, friendly WhatsApp marketing messages."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
        )
        return response.choices[0].message.content or f"Hi {customer.name or 'there'}! We miss you at {merchant.name}. Enjoy {discount_pct}% OFF today!"
    except Exception as exc:
        logger.error("Failed to generate campaign message with Groq: %s", exc)
        return f"Hi {customer.name or 'there'}! We miss you at {merchant.name}. Use code TREAT{discount_pct} for {discount_pct}% OFF your next order!"


async def dispatch_campaign_to_customer(
    db: AsyncSession,
    merchant: Merchant,
    customer: Customer,
    offer_text: str,
    discount_pct: int = 15,
) -> Campaign:
    """Create campaign record, generate personalized message, and dispatch via WhatsApp."""
    message = await generate_personalized_reengagement(merchant, customer, discount_pct)

    # Generate sample promotional Razorpay payment link for voucher/store credit
    rzp_link = None
    try:
        link_data = razorpay_service.create_payment_link(
            amount_inr=500 * (1 - discount_pct / 100),
            description=f"{merchant.name} VIP Discount Voucher",
            customer_name=customer.name,
            customer_phone=customer.phone,
            reference_id=f"camp_{uuid.uuid4().hex[:10]}",
        )
        rzp_link = link_data.get("short_url") or link_data.get("url")
    except Exception as exc:
        logger.warning("Could not generate Razorpay link for campaign: %s", exc)

    # Send WhatsApp text
    full_text = message
    if rzp_link:
        full_text += f"\n\n🎁 Claim VIP voucher: {rzp_link}"

    await whatsapp_service.send_text_message(to=customer.phone, text=full_text)

    campaign = Campaign(
        id=uuid.uuid4(),
        merchant_id=merchant.id,
        customer_id=customer.id,
        campaign_type="re_engagement",
        offer=f"{discount_pct}% Discount Offer",
        message_text=full_text,
        rzp_link=rzp_link,
        status="sent",
    )
    db.add(campaign)
    await db.commit()
    await db.refresh(campaign)
    return campaign
