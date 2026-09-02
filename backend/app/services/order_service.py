"""Order lifecycle, Razorpay transaction processing, and Budget Guardrails service."""

import re
import uuid
import logging
from datetime import datetime, timezone
from typing import Any
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
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
    fulfillment_mode: str = "delivery",
    delivery_address: str | None = None,
    delivery_latitude: float | None = None,
    delivery_longitude: float | None = None,
    pickup_time: str | None = None,
    client_items: list[dict[str, Any]] | None = None,
) -> Order:
    """Create a database Order from conversation cart, apply Budget Guardrails, and generate Razorpay link."""
    # 1. Fetch conversation
    stmt = select(Conversation).where(Conversation.id == conversation_id)
    res = await db.execute(stmt)
    conv = res.scalar_one_or_none()
    if not conv:
        raise ValueError(f"Conversation {conversation_id} not found")

    if conv.merchant_id != merchant_id:
        conv.merchant_id = merchant_id

    cart = conv.cart or {}
    items = cart.get("items", [])
    if not items and client_items and len(client_items) > 0:
        # Client synchronized items
        items = client_items
        calc_total = sum(float(i.get("unit_price") or i.get("price", 0)) * int(i.get("quantity", 1)) for i in items)
        cart = {"items": items, "total": calc_total}
        conv.cart = cart

    if not items:
        raise ValueError("Cannot checkout with an empty cart. Please add items first.")

    total = float(cart.get("total", 0.0))
    if total <= 0:
        total = sum(float(i.get("unit_price") or i.get("price", 0)) * int(i.get("quantity", 1)) for i in items)
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

    # 4. Execute Transactional Checkout Saga (Idempotency + Row-Locked Inventory + Auto-Compensation)
    from app.services.checkout_saga import checkout_saga

    order = await checkout_saga.execute_checkout(
        db=db,
        conversation_id=conversation_id,
        merchant_id=merchant_id,
        items=items,
        total=round(total, 2),
        subtotal=round(subtotal, 2),
        customer_name=customer_name,
        customer_phone=customer_phone,
        customer_email=customer_email,
        callback_url=callback_url,
        fulfillment_mode=fulfillment_mode,
        delivery_address=delivery_address,
        delivery_latitude=delivery_latitude,
        delivery_longitude=delivery_longitude,
        pickup_time=pickup_time,
    )

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


def calculate_haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate great-circle distance between two geographical points using Haversine formula."""
    import math
    R = 6371.0  # Earth's radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 2)




# ═══════════════════════════════════════════════════════════════
# Category-based preparation time mapping (in minutes)
# ═══════════════════════════════════════════════════════════════
CATEGORY_PREP_MINUTES: dict[str, int] = {
    # Quick grab (pre-made bakery items)
    "Cakes": 5,
    "Pastries": 5,
    "Breads": 3,
    "Beverages": 5,
    "Party Supplies": 2,
    "Combos": 10,
    # Grocery / quick-pack
    "Fruits": 3,
    "Vegetables": 3,
    "Dairy": 3,
    "Snacks": 3,
    "Pantry": 3,
    "Breakfast": 5,
    # Cooked food (longer prep)
    "Main Course": 25,
    "Starters": 15,
    "Biryani": 30,
    "Chinese": 20,
    "South Indian": 15,
    "North Indian": 25,
    "Desserts": 10,
}

# Delivery partner name pool (deterministic via order ID hash)
DRIVER_NAMES = [
    "Ramesh Kumar", "Suresh Gowda", "Venkatesh M", "Anil Sharma",
    "Rajesh Yadav", "Manoj Kumar", "Deepak S", "Harish Babu",
    "Pradeep Raj", "Naveen Kumar", "Sanjay Reddy", "Kiran Hegde",
    "Mohan Das", "Ravi Shankar", "Ganesh Rao",
]

DRIVER_VEHICLES = [
    ("Hero Electric Optima", "KA 05 MN 4821"),
    ("Ola Electric S1", "KA 01 AB 9342"),
    ("TVS iQube", "KA 03 CD 7712"),
    ("Bajaj Chetak EV", "KA 05 EF 1156"),
    ("Ather 450X", "KA 02 GH 3378"),
    ("Hero Splendor", "KA 04 JK 2290"),
    ("Honda Activa", "KA 51 LM 5501"),
    ("TVS Jupiter", "KA 53 NP 8847"),
    ("Yamaha FZ", "KA 05 QR 6623"),
    ("Royal Enfield Classic", "KA 01 ST 4459"),
]


def _compute_prep_time_from_items(items: list[dict]) -> int:
    """Return max prep time in minutes across all items based on their category."""
    max_prep = 5  # minimum baseline
    for item in items:
        cat = item.get("category", "")
        prep = CATEGORY_PREP_MINUTES.get(cat, 8)
        if prep > max_prep:
            max_prep = prep
    return max_prep


def _generate_pickup_otp(order_id: uuid.UUID) -> str:
    """Generate a deterministic 4-digit OTP from order ID."""
    import hashlib
    h = hashlib.md5(str(order_id).encode()).hexdigest()
    return str(int(h[:8], 16) % 9000 + 1000)


def _select_driver(order_id: uuid.UUID) -> tuple[str, str, str]:
    """Deterministically select driver name + vehicle from pool based on order ID."""
    idx = int(str(order_id).replace("-", "")[:8], 16) % len(DRIVER_NAMES)
    vidx = int(str(order_id).replace("-", "")[8:16], 16) % len(DRIVER_VEHICLES)
    vehicle_name, vehicle_plate = DRIVER_VEHICLES[vidx]
    return DRIVER_NAMES[idx], vehicle_name, vehicle_plate


def _compute_current_stage(
    is_pickup: bool,
    elapsed_minutes: int,
    prep_time_minutes: int,
    total_eta_minutes: int,
) -> str:
    """Compute the current order stage based on elapsed time and prep time."""
    if is_pickup:
        if elapsed_minutes < prep_time_minutes * 0.5:
            return "preparing"
        elif elapsed_minutes < prep_time_minutes:
            return "almost_ready"
        else:
            return "ready_for_pickup"
    else:
        if elapsed_minutes < prep_time_minutes:
            return "preparing"
        elif elapsed_minutes < total_eta_minutes * 0.9:
            return "out_for_delivery"
        else:
            return "arriving"


async def get_order_tracking_data(db: AsyncSession, order_id: uuid.UUID) -> dict[str, Any] | None:
    """Calculate and return real dynamic tracking telemetry using store coordinates, Haversine math, and category-based prep time."""
    import math
    order = await get_order_by_id(db, order_id)
    if not order:
        return None

    # Fetch merchant details
    from app.models.merchant import Merchant
    m_stmt = select(Merchant).where(Merchant.id == order.merchant_id)
    m_res = await db.execute(m_stmt)
    merchant = m_res.scalar_one_or_none()

    store_lat = (merchant.store_latitude if merchant and merchant.store_latitude else 12.9716)
    store_lng = (merchant.store_longitude if merchant and merchant.store_longitude else 77.6412)
    store_addr = (merchant.store_address if merchant and merchant.store_address else "100ft Road, Indiranagar, Bengaluru")
    store_name = merchant.name if merchant else "Sweet Bakes Bakery"

    customer_lat = order.delivery_latitude or 12.9550
    customer_lng = order.delivery_longitude or 77.6520

    is_pickup = (order.fulfillment_mode == "pickup")

    # Dynamic prep time from item categories
    items = order.items or []
    prep_time_min = _compute_prep_time_from_items(items)

    # Haversine distance
    dist_km = calculate_haversine_distance_km(store_lat, store_lng, customer_lat, customer_lng)
    
    # Real ETA calculation: urban velocity + dynamic prep buffer
    avg_speed_kmh = 24.0
    travel_time_min = (dist_km / avg_speed_kmh) * 60.0
    total_eta_min = math.ceil(prep_time_min + travel_time_min) if not is_pickup else prep_time_min

    # Elapsed time calculation
    now = datetime.now(timezone.utc)
    order_created = order.created_at or now
    if order_created.tzinfo is None:
        order_created = order_created.replace(tzinfo=timezone.utc)
    elapsed_seconds = (now - order_created).total_seconds()
    elapsed_minutes = max(0, int(elapsed_seconds / 60))

    remaining_eta = max(1, total_eta_min - elapsed_minutes)
    
    # Dynamic live progress percentage
    if order.status == OrderStatus.PAID:
        progress_pct = min(95, max(10, int((elapsed_minutes / max(1, total_eta_min)) * 100)))
    else:
        progress_pct = 10

    # Current stage
    current_stage = _compute_current_stage(is_pickup, elapsed_minutes, prep_time_min, total_eta_min)

    # Driver info (deterministic per order)
    driver_name, vehicle_name, vehicle_plate = _select_driver(order.id)

    # Pickup OTP (deterministic per order)
    pickup_otp = _generate_pickup_otp(order.id)

    return {
        "order_id": str(order.id),
        "status": order.status.value if hasattr(order.status, "value") else str(order.status),
        "fulfillment_mode": order.fulfillment_mode or "delivery",
        "store_name": store_name,
        "store_address": store_addr,
        "store_latitude": store_lat,
        "store_longitude": store_lng,
        "customer_latitude": customer_lat,
        "customer_longitude": customer_lng,
        "haversine_distance_km": dist_km,
        "average_speed_kmh": avg_speed_kmh,
        "prep_time_minutes": prep_time_min,
        "total_estimated_eta_minutes": total_eta_min,
        "remaining_eta_minutes": remaining_eta,
        "elapsed_minutes": elapsed_minutes,
        "live_progress_percentage": progress_pct,
        "current_stage": current_stage,
        "is_pickup": is_pickup,
        "driver_name": driver_name,
        "driver_vehicle": f"{vehicle_name} • {vehicle_plate}",
        "pickup_otp": pickup_otp,
        "created_at": order_created.isoformat(),
        "rzp_payment_id": order.rzp_payment_id,
        "total": order.total,
        "delivery_address": order.delivery_address,
    }


# Convenience alias for agent workflows
create_order = create_order_from_conversation
