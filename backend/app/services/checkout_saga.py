"""Checkout Saga Service — Distributed transaction pattern for failure-proof checkout and stock compensation."""

import logging
import uuid
from typing import Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.merchant import Merchant
from app.models.product import Product
from app.models.order import Order, OrderStatus
from app.models.conversation import Conversation
from app.models.audit_log import AuditLog
from app.services.audit_service import log_audit_event, AuditEventType
from app.services.razorpay_service import razorpay_service
from app.services.idempotency_service import idempotency_service

logger = logging.getLogger(__name__)


class CheckoutSagaError(Exception):
    """Raised when a checkout saga fails and triggers compensation."""
    pass


class CheckoutSaga:
    """Executes a 3-phase checkout saga with automated stock compensation."""

    @staticmethod
    async def execute_checkout(
        db: AsyncSession,
        conversation_id: uuid.UUID,
        merchant_id: uuid.UUID,
        items: list[dict[str, Any]],
        total: float,
        subtotal: float,
        customer_name: str | None = None,
        customer_phone: str | None = None,
        customer_email: str | None = None,
        callback_url: str | None = None,
        fulfillment_mode: str = "delivery",
        delivery_address: str | None = None,
        delivery_latitude: float | None = None,
        delivery_longitude: float | None = None,
        pickup_time: str | None = None,
    ) -> Order:
        """Execute the checkout saga.
        
        Step 1: Check Idempotency Cache
        Step 2: Phase 1 — Row-locked stock reservation
        Step 3: Phase 2 — Razorpay Order and Payment Link Creation
        Step 4: Phase 3 — Commit Order and log audit trail
        Compensation: If Phase 2/3 fails, restore reserved stock immediately.
        """
        # Step 1: Check Idempotency Key
        idemp_key = idempotency_service.generate_checkout_key(conversation_id, merchant_id, items, total)
        cached_resp = await idempotency_service.get_cached_response(idemp_key)
        if cached_resp and "order_id" in cached_resp:
            logger.info("Checkout Saga: Returning existing idempotent order %s", cached_resp["order_id"])
            existing_order_id = uuid.UUID(cached_resp["order_id"])
            stmt = select(Order).where(Order.id == existing_order_id)
            res = await db.execute(stmt)
            existing_order = res.scalar_one_or_none()
            if existing_order:
                return existing_order

        # Verify Merchant
        stmt_m = select(Merchant).where(Merchant.id == merchant_id)
        res_m = await db.execute(stmt_m)
        merchant = res_m.scalar_one_or_none()
        if not merchant:
            raise ValueError(f"Merchant {merchant_id} not found")

        # Step 2: Phase 1 — Row-locked stock reservation & Database-Authoritative Pricing
        reserved_items: list[dict[str, Any]] = []
        verified_items: list[dict[str, Any]] = []
        authoritative_total = 0.0

        try:
            for item in items:
                raw_pid = item.get("product_id")
                if not raw_pid:
                    continue
                pid = uuid.UUID(str(raw_pid))
                qty = int(item.get("quantity", 1))

                # Row-level lock on Product (lookup by ID first to tolerate discovery mode merchant mismatches)
                stmt_p = select(Product).where(Product.id == pid).with_for_update()
                res_p = await db.execute(stmt_p)
                product = res_p.scalar_one_or_none()

                if product:
                    # If product belongs to another merchant (e.g. from All Stores discovery), auto-align to product's true store
                    if product.merchant_id != merchant_id:
                        logger.info("Auto-aligning checkout merchant from %s to product's actual merchant %s (%s)", merchant_id, product.merchant_id, product.name)
                        merchant_id = product.merchant_id
                        stmt_m = select(Merchant).where(Merchant.id == merchant_id)
                        res_m = await db.execute(stmt_m)
                        real_merchant = res_m.scalar_one_or_none()
                        if real_merchant:
                            merchant = real_merchant

                    if not product.in_stock or (product.stock_quantity is not None and product.stock_quantity < qty):
                        avail = product.stock_quantity if product.stock_quantity is not None else 0
                        raise ValueError(
                            f"Insufficient stock for '{product.name}'. Available: {avail}, requested: {qty}"
                        )

                    # SERVER-SIDE PRICE IMMUTABILITY: Use exact database catalog price
                    verified_price = float(product.price)
                    authoritative_total += verified_price * qty
                    verified_items.append({
                        "product_id": str(pid),
                        "name": product.name,
                        "price": verified_price,
                        "unit_price": verified_price,
                        "quantity": qty,
                        "category": product.category,
                    })

                    if product.stock_quantity is not None:
                        # Decrement stock atomically under exclusive row lock
                        product.stock_quantity -= qty
                        if product.stock_quantity <= 0:
                            product.stock_quantity = 0
                            product.in_stock = False
                        reserved_items.append({"product_id": pid, "quantity": qty, "product": product})
                    else:
                        # Unlimited stock items
                        reserved_items.append({"product_id": pid, "quantity": qty, "product": product})
                else:
                    raise ValueError(f"Product {pid} not found for merchant {merchant_id}")

            await db.flush()
            logger.info("Checkout Saga Phase 1 SUCCESS: Reserved %d items for merchant %s (Authoritative Total: ₹%.2f)", len(reserved_items), merchant.name, authoritative_total)

        except Exception as phase1_err:
            logger.error("Checkout Saga Phase 1 FAILED (Stock Reservation): %s", phase1_err)
            # Revert any partially decremented items in session
            for r in reserved_items:
                if "product" in r and r["product"].stock_quantity is not None:
                    r["product"].stock_quantity += r["quantity"]
                    if r["product"].stock_quantity > 0:
                        r["product"].in_stock = True
            await db.rollback()
            raise phase1_err

        # Use verified total computed from PostgreSQL
        final_total = round(authoritative_total if authoritative_total > 0 else total, 2)
        final_items = verified_items if len(verified_items) > 0 else items

        # Step 3: Phase 2 — Razorpay Order & Payment Link Creation
        order_id = uuid.uuid4()
        rzp_order_id = None
        rzp_payment_link_id = None
        payment_link_url = None

        try:
            # 1. Create Razorpay Order with authoritative database amount
            rzp_order = razorpay_service.create_order(
                amount_inr=final_total,
                receipt=f"rcpt_{str(order_id)[:12]}",
                notes={
                    "order_id": str(order_id),
                    "merchant_id": str(merchant_id),
                    "conversation_id": str(conversation_id),
                    "fulfillment_mode": fulfillment_mode,
                    "idempotency_key": idemp_key,
                },
            )
            rzp_order_id = rzp_order.get("id")

            # 2. Create Razorpay Payment Link
            link_desc = f"Order #{str(order_id)[:8]} at {merchant.name}"
            rzp_link = razorpay_service.create_payment_link(
                amount_inr=final_total,
                description=link_desc,
                customer_name=customer_name or "Valued Customer",
                customer_phone=customer_phone or merchant.phone or "+919876543210",
                customer_email=customer_email or "customer@example.com",
                callback_url=callback_url,
                notes={
                    "order_id": str(order_id),
                    "merchant_id": str(merchant_id),
                    "rzp_order_id": rzp_order_id or "",
                },
            )
            rzp_payment_link_id = rzp_link.get("id")
            payment_link_url = rzp_link.get("short_url")

            # Route to our hosted mobile-optimized Razorpay checkout terminal
            # if test mode quota limit of 30 was reached (returning mock rzp.io/i/ links)
            from app.config import settings
            if not payment_link_url or "rzp.io/i/" in payment_link_url or "rzp.io/rzp/" not in payment_link_url:
                payment_link_url = f"{settings.resolved_public_backend_url}/pay/{order_id}?ngrok-skip-browser-warning=1"

            logger.info("Checkout Saga Phase 2 SUCCESS: Razorpay link generated: %s", payment_link_url)

        except Exception as phase2_err:
            # COMPENSATION TRIGGERED
            logger.error("Checkout Saga Phase 2 FAILED (Razorpay API). Triggering COMPENSATION rollback: %s", phase2_err)
            for res_item in reserved_items:
                prod = res_item["product"]
                if prod and prod.stock_quantity is not None:
                    prod.stock_quantity += res_item["quantity"]
                    prod.in_stock = True
            await db.flush()

            await log_audit_event(
                db=db,
                event_type=AuditEventType.AGENT_DECISION,
                merchant_id=merchant_id,
                conversation_id=conversation_id,
                action="checkout_saga_compensation_rollback",
                reasoning=f"Payment link creation failed ({phase2_err}). Automatically restored stock for {len(reserved_items)} reserved items.",
                input_data={"reserved_items_count": len(reserved_items), "error": str(phase2_err)},
            )
            raise CheckoutSagaError(f"Payment gateway initialization failed: {phase2_err}. Stock was safely released.") from phase2_err

        # Step 4: Phase 3 — Finalize Order in Database
        order = Order(
            id=order_id,
            merchant_id=merchant_id,
            conversation_id=conversation_id,
            items=final_items,
            subtotal=final_total,
            total=final_total,
            subtotal_paise=int(round(final_total * 100)),
            total_paise=int(round(final_total * 100)),
            rzp_order_id=rzp_order_id,
            rzp_payment_link_id=rzp_payment_link_id,
            payment_link=payment_link_url,
            status=OrderStatus.PAYMENT_LINK_SENT,
            fulfillment_mode=fulfillment_mode,
            delivery_address=delivery_address,
            delivery_latitude=delivery_latitude,
            delivery_longitude=delivery_longitude,
            pickup_time=pickup_time,
            audit_trail=[
                {
                    "action": "checkout_saga_completed",
                    "status": "payment_link_sent",
                    "idempotency_key": idemp_key,
                    "payment_link": payment_link_url,
                    "timestamp": str(uuid.uuid1()),
                }
            ],
        )
        db.add(order)
        await db.commit()
        await db.refresh(order)

        # Record audit log in PostgreSQL
        await log_audit_event(
            db=db,
            event_type=AuditEventType.CHECKOUT_INITIATED,
            merchant_id=merchant_id,
            conversation_id=conversation_id,
            order_id=order.id,
            action="checkout_saga_order_created",
            reasoning=f"Order created with total ₹{total}. Idempotency key: {idemp_key}",
            input_data={"items_count": len(items), "total": total, "idempotency_key": idemp_key},
            output_data={"order_id": str(order.id), "rzp_order_id": rzp_order_id, "payment_link": payment_link_url},
        )

        # Record idempotency
        await idempotency_service.record_response(
            idemp_key,
            {
                "order_id": str(order.id),
                "rzp_order_id": rzp_order_id,
                "payment_link": payment_link_url,
                "total": total,
            },
        )

        logger.info("Checkout Saga COMPLETE: Order %s created with payment link %s", order.id, payment_link_url)
        return order


checkout_saga = CheckoutSaga()
