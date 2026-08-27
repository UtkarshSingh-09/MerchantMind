"""Order lifecycle, Razorpay transaction processing, and Budget Guardrails service."""

import re
import uuid
import logging
from datetime import datetime, timezone
from typing import Any
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import Order, OrderStatus
from app.models.conversation import Conversation
from app.models.merchant import Merchant
from app.models.customer import Customer
from app.services.razorpay_service import razorpay_service
from app.services.audit_service import log_audit_event, AuditEventType

logger = logging.getLogger(__name__)


def extract_customer_budget(messages: list[dict[str, Any]]) -> float | None:
    """Extract explicit customer budget limit from conversation text if stated."""
    # Pattern matching: "under 800", "budget 800", "within ₹800", "under ₹ 800", "max 800", "budget is 800"
    pattern = re.compile(
        r"(?:under|budget\s*(?:is|of|:)?|within|below|max|maximum)\s*(?:₹|rs\.?|inr)?\s*(\d+(?:\.\d+)?)",
        re.IGNORECASE,
    )
    for msg in reversed(messages or []):
        if msg.get("role") == "user":
            content = msg.get("content", "")
            match = pattern.search(content)
            if match:
                try:
                    val = float(match.group(1))
                    if 10 <= val <= 1000000:  # Sensible range
                        return val
                except ValueError:
                    continue
    return None


async def create_order_from_conversation(
    db: AsyncSession,
    conversation_id: uuid.UUID,
    merchant_id: uuid.UUID,
    customer_name: str | None = None,
    customer_phone: str | None = None,
    customer_email: str | None = None,
    callback_url: str | None = None,
    budget_limit: float | None = None,
) -> Order:
    """Create a database Order from conversation cart, apply Budget Guardrails, and generate Razorpay link."""
    # 1. Fetch conversation
    stmt = select(Conversation).where(
        Conversation.id == conversation_id,
        Conversation.merchant_id == merchant_id,
    )
    res = await db.execute(stmt)
    conv = res.scalar_one_or_none()
    if not conv:
        raise ValueError(f"Conversation {conversation_id} not found for merchant {merchant_id}")

    cart = conv.cart or {}
    items = cart.get("items", [])
    if not items:
        raise ValueError("Cannot checkout with an empty cart. Please add items first.")

    total = float(cart.get("total", 0.0))
    if total <= 0:
        total = sum(float(i.get("price", 0)) * int(i.get("quantity", 1)) for i in items)
    subtotal = total

    # 2. Budget Enforcement Guardrail
    detected_budget = budget_limit or extract_customer_budget(conv.messages or [])
    if detected_budget is not None:
        if total > detected_budget:
            await log_audit_event(
                db=db,
                event_type=AuditEventType.BUDGET_VIOLATION,
                merchant_id=merchant_id,
                conversation_id=conversation_id,
                action="checkout_blocked_budget_exceeded",
                reasoning=f"Hard guardrail triggered: Cart total ₹{total:.2f} exceeds customer's stated budget of ₹{detected_budget:.2f}",
                input_data={"cart_total": total, "budget_limit": detected_budget, "items": items},
                output_data={"blocked": True},
            )
            await db.commit()
            raise ValueError(
                f"Budget Guardrail: Cart total of ₹{total:.2f} exceeds your stated budget limit of ₹{detected_budget:.2f}. "
                f"Please remove some items or adjust your selection before proceeding to payment."
            )
        else:
            await log_audit_event(
                db=db,
                event_type=AuditEventType.BUDGET_CHECK,
                merchant_id=merchant_id,
                conversation_id=conversation_id,
                action="budget_compliance_verified",
                reasoning=f"Cart total ₹{total:.2f} is within customer's stated budget ₹{detected_budget:.2f}",
                input_data={"cart_total": total, "budget_limit": detected_budget},
                output_data={"allowed": True},
            )

    # 3. Fetch or link customer
    customer_id = conv.customer_id
    if not customer_id and (customer_phone or customer_email):
        cust_stmt = select(Customer).where(
            Customer.merchant_id == merchant_id,
            or_(
                Customer.phone == customer_phone if customer_phone else False,
                Customer.email == customer_email if customer_email else False,
            ),
        )
        cust_res = await db.execute(cust_stmt)
        existing_cust = cust_res.scalar_one_or_none()
        if existing_cust:
            customer_id = existing_cust.id
        else:
            new_cust = Customer(
                merchant_id=merchant_id,
                name=customer_name or "Guest Customer",
                phone=customer_phone or "unknown",
                email=customer_email,
            )
            db.add(new_cust)
            await db.flush()
            customer_id = new_cust.id
            conv.customer_id = customer_id

    # 4. Create initial database Order
    order_id = uuid.uuid4()
    audit_entry = {
        "action": "order_created",
        "reasoning": f"Checkout initiated. Cart has {len(items)} items for ₹{total:.2f}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    order = Order(
        id=order_id,
        merchant_id=merchant_id,
        customer_id=customer_id,
        conversation_id=conversation_id,
        items=items,
        subtotal=round(subtotal, 2),
        total=round(total, 2),
        status=OrderStatus.PENDING,
        audit_trail=[audit_entry],
    )
    db.add(order)
    await db.flush()

    await log_audit_event(
        db=db,
        event_type=AuditEventType.CHECKOUT_INITIATED,
        merchant_id=merchant_id,
        order_id=order_id,
        conversation_id=conversation_id,
        action="order_created",
        reasoning=f"Order created with total ₹{total:.2f}",
        input_data={"items": items, "total": total},
        output_data={"order_id": str(order_id), "status": "pending"},
    )

    # 5. Generate Razorpay Order
    rzp_order_id = None
    try:
        rzp_order = razorpay_service.create_order(
            amount_inr=total,
            receipt=f"rcpt_{str(order_id)[:8]}",
            notes={
                "order_id": str(order_id),
                "merchant_id": str(merchant_id),
                "conversation_id": str(conversation_id),
            },
        )
        rzp_order_id = rzp_order.get("id")
        order.rzp_order_id = rzp_order_id

        await log_audit_event(
            db=db,
            event_type=AuditEventType.RAZORPAY_ORDER,
            merchant_id=merchant_id,
            order_id=order_id,
            conversation_id=conversation_id,
            action="razorpay_order_created",
            reasoning=f"Created Razorpay order {rzp_order_id} for ₹{total:.2f}",
            input_data={"amount_inr": total},
            output_data=rzp_order,
        )
    except Exception as exc:
        logger.warning("Could not create Razorpay Order via SDK: %s. Using direct payment link.", exc)

    # 6. Generate Razorpay Payment Link
    payment_link_url = None
    rzp_link_id = None
    try:
        link_data = razorpay_service.create_payment_link(
            amount_inr=total,
            description=f"Order #{str(order_id)[:8]} payment",
            customer_name=customer_name,
            customer_email=customer_email,
            customer_phone=customer_phone,
            reference_id=f"order_{str(order_id)[:12]}",
            callback_url=callback_url,
            notes={"order_id": str(order_id)},
        )
        payment_link_url = link_data.get("short_url") or link_data.get("url")
        rzp_link_id = link_data.get("id")

        await log_audit_event(
            db=db,
            event_type=AuditEventType.RAZORPAY_PAYMENT_LINK,
            merchant_id=merchant_id,
            order_id=order_id,
            conversation_id=conversation_id,
            action="razorpay_payment_link_generated",
            reasoning=f"Generated shareable payment link {payment_link_url}",
            input_data={"total": total, "reference_id": f"order_{str(order_id)[:12]}"},
            output_data={"payment_link": payment_link_url, "link_id": rzp_link_id},
        )
    except Exception as exc:
        logger.warning("Payment link creation encountered exception: %s. Generating test payment link.", exc)
        payment_link_url = f"https://rzp.io/i/test_{str(order_id)[:8]}"

    order.payment_link = payment_link_url
    order.rzp_payment_link_id = rzp_link_id
    order.status = OrderStatus.PAYMENT_LINK_SENT

    order.audit_trail.append({
        "action": "payment_link_generated",
        "payment_link": payment_link_url,
        "rzp_order_id": rzp_order_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

    await db.commit()
    await db.refresh(order)
    return order


async def handle_payment_captured(
    db: AsyncSession,
    rzp_order_id: str | None = None,
    rzp_payment_id: str | None = None,
    rzp_link_id: str | None = None,
    order_id: uuid.UUID | None = None,
    amount_paid: float | None = None,
) -> Order | None:
    """Handle payment capture event from webhook or payment verification."""
    stmt = select(Order)
    if order_id:
        stmt = stmt.where(Order.id == order_id)
    elif rzp_order_id:
        stmt = stmt.where(Order.rzp_order_id == rzp_order_id)
    elif rzp_link_id:
        stmt = stmt.where(Order.rzp_payment_link_id == rzp_link_id)
    else:
        return None

    res = await db.execute(stmt)
    order = res.scalar_one_or_none()
    if not order:
        logger.warning("No matching order found for payment capture: rzp_order_id=%s, link_id=%s", rzp_order_id, rzp_link_id)
        return None

    if order.status == OrderStatus.PAID:
        logger.info("Order %s already marked as PAID.", order.id)
        return order

    order.status = OrderStatus.PAID
    order.rzp_payment_id = rzp_payment_id
    order.paid_at = datetime.now(timezone.utc)

    audit = list(order.audit_trail or [])
    audit.append({
        "action": "payment_captured",
        "rzp_payment_id": rzp_payment_id,
        "amount": amount_paid or order.total,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    order.audit_trail = audit

    await log_audit_event(
        db=db,
        event_type=AuditEventType.PAYMENT_CAPTURED,
        merchant_id=order.merchant_id,
        order_id=order.id,
        conversation_id=order.conversation_id,
        action="payment_captured",
        reasoning=f"Payment verified via Razorpay webhook. Total ₹{order.total:.2f} received.",
        input_data={"rzp_order_id": rzp_order_id, "rzp_payment_id": rzp_payment_id, "amount": amount_paid},
        output_data={"status": "paid", "paid_at": order.paid_at.isoformat()},
    )

    if order.conversation_id:
        conv_stmt = select(Conversation).where(Conversation.id == order.conversation_id)
        c_res = await db.execute(conv_stmt)
        conv = c_res.scalar_one_or_none()
        if conv:
            conv.status = "completed"
            conv.cart = {"items": [], "total": 0.0}

    await db.commit()
    await db.refresh(order)
    logger.info("Successfully marked Order %s as PAID (payment_id: %s)", order.id, rzp_payment_id)
    return order


async def handle_payment_failed(
    db: AsyncSession,
    rzp_order_id: str | None = None,
    rzp_link_id: str | None = None,
    order_id: uuid.UUID | None = None,
    error_reason: str | None = None,
) -> Order | None:
    """Handle payment failure event from webhook."""
    stmt = select(Order)
    if order_id:
        stmt = stmt.where(Order.id == order_id)
    elif rzp_order_id:
        stmt = stmt.where(Order.rzp_order_id == rzp_order_id)
    elif rzp_link_id:
        stmt = stmt.where(Order.rzp_payment_link_id == rzp_link_id)
    else:
        return None

    res = await db.execute(stmt)
    order = res.scalar_one_or_none()
    if not order:
        return None

    order.status = OrderStatus.FAILED
    audit = list(order.audit_trail or [])
    audit.append({
        "action": "payment_failed",
        "reason": error_reason or "Payment declined by issuing bank / gateway",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    order.audit_trail = audit

    await log_audit_event(
        db=db,
        event_type=AuditEventType.PAYMENT_FAILED,
        merchant_id=order.merchant_id,
        order_id=order.id,
        conversation_id=order.conversation_id,
        action="payment_failed",
        reasoning=f"Payment declined: {error_reason}",
        input_data={"rzp_order_id": rzp_order_id, "error_reason": error_reason},
        output_data={"status": "failed"},
    )

    await db.commit()
    await db.refresh(order)
    return order


async def get_order_by_id(db: AsyncSession, order_id: uuid.UUID) -> Order | None:
    """Fetch order by UUID."""
    stmt = select(Order).where(Order.id == order_id)
    res = await db.execute(stmt)
    return res.scalar_one_or_none()
