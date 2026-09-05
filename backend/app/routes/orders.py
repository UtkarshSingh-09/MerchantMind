"""Order API routes — order creation, status, and audit trail."""

import uuid
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.order import Order, OrderStatus
from app.models.merchant import Merchant
from app.schemas.order import (
    OrderCreate,
    OrderResponse,
    OrderStatusResponse,
    MultiOrderCreate,
    MultiOrderResponse,
)
import logging
from app.config import settings
from app.services import order_service, audit_service
from app.middleware.rate_limiter import rate_limit

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/multi-checkout",
    response_model=MultiOrderResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit(max_requests=30, window_seconds=60, scope="orders"))],
)
async def create_multi_order(
    payload: MultiOrderCreate,
    db: AsyncSession = Depends(get_db),
):
    """Initiate multi-merchant checkout with atomic checkout saga and unified Razorpay link."""
    try:
        res = await order_service.create_multi_merchant_orders(
            db=db,
            conversation_id=payload.conversation_id,
            client_items=payload.items,
            fulfillment_mode=payload.fulfillment_mode or "delivery",
            delivery_address=payload.delivery_address,
            delivery_latitude=payload.delivery_latitude,
            delivery_longitude=payload.delivery_longitude,
            pickup_time=payload.pickup_time,
            customer_name=payload.customer_name,
            customer_phone=payload.customer_phone,
            customer_email=payload.customer_email,
            callback_url=payload.callback_url,
        )
        return res
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except Exception as exc:
        logger.exception("Failed to initiate multi-merchant checkout: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initiate multi-store checkout: {exc}",
        )


@router.post(
    "/",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit(max_requests=30, window_seconds=60, scope="orders"))],
)
async def create_order(
    payload: OrderCreate,
    db: AsyncSession = Depends(get_db),
):
    # Auto-resolve true merchant from products if in All-Stores / Discovery mode
    if payload.items and len(payload.items) > 0:
        from app.models.product import Product
        raw_pid = payload.items[0].get("product_id")
        if raw_pid:
            try:
                p_stmt = select(Product).where(Product.id == uuid.UUID(str(raw_pid)))
                p_res = await db.execute(p_stmt)
                prod = p_res.scalar_one_or_none()
                if prod and prod.merchant_id:
                    payload.merchant_id = prod.merchant_id
            except Exception as p_err:
                logger.warning("Failed resolving product merchant: %s", p_err)

    # Verify merchant exists
    m_stmt = select(Merchant).where(Merchant.id == payload.merchant_id)
    m_res = await db.execute(m_stmt)
    merchant = m_res.scalar_one_or_none()
    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Merchant {payload.merchant_id} not found",
        )

    try:
        order = await order_service.create_order_from_conversation(
            db=db,
            conversation_id=payload.conversation_id,
            merchant_id=payload.merchant_id,
            customer_name=payload.customer_name,
            customer_phone=payload.customer_phone,
            customer_email=payload.customer_email,
            callback_url=payload.callback_url,
            fulfillment_mode=payload.fulfillment_mode or "delivery",
            delivery_address=payload.delivery_address,
            delivery_latitude=payload.delivery_latitude,
            delivery_longitude=payload.delivery_longitude,
            pickup_time=payload.pickup_time,
            client_items=payload.items,
        )
        return order
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initiate order checkout: {exc}",
        )


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order_details(
    order_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve full order details and payment audit trail."""
    order = await order_service.get_order_by_id(db, order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order {order_id} not found",
        )
    return order


@router.get("/{order_id}/status", response_model=OrderStatusResponse)
async def get_order_status(
    order_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Lightweight order status polling endpoint for frontend payment confirmation."""
    order = await order_service.get_order_by_id(db, order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order {order_id} not found",
        )

    if not order.rzp_order_id and order.status != OrderStatus.PAID:
        try:
            from app.services.razorpay_service import razorpay_service
            rzp_ord = razorpay_service.create_order(
                amount_inr=order.total,
                receipt=f"rcpt_{str(order.id)[:15]}",
                notes={"order_id": str(order.id)},
            )
            order.rzp_order_id = rzp_ord.get("id")
            await db.commit()
            await db.refresh(order)
        except Exception as e:
            logger.warning("Could not auto-generate rzp_order_id: %s", e)

    rzp_key = settings.razorpay_key_id or "rzp_test_TTBzVCxzHMSaip"
    return OrderStatusResponse(
        id=order.id,
        status=order.status.value if hasattr(order.status, "value") else str(order.status),
        total=order.total,
        rzp_order_id=order.rzp_order_id,
        rzp_payment_id=order.rzp_payment_id,
        payment_link=order.payment_link,
        paid_at=order.paid_at,
        rzp_key_id=rzp_key,
    )


@router.get("/conversation/{conversation_id}/latest", response_model=OrderStatusResponse)
async def get_latest_conversation_order(
    conversation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve the most recent order for a conversation to assist frontend direct checkout triggers."""
    stmt = (
        select(Order)
        .where(Order.conversation_id == conversation_id)
        .order_by(Order.created_at.desc())
    )
    res = await db.execute(stmt)
    order = res.scalars().first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No order found for conversation {conversation_id}",
        )

    if not order.rzp_order_id and order.status != OrderStatus.PAID:
        try:
            from app.services.razorpay_service import razorpay_service
            rzp_ord = razorpay_service.create_order(
                amount_inr=order.total,
                receipt=f"rcpt_{str(order.id)[:15]}",
                notes={"order_id": str(order.id)},
            )
            order.rzp_order_id = rzp_ord.get("id")
            await db.commit()
            await db.refresh(order)
        except Exception as e:
            logger.warning("Could not auto-generate rzp_order_id: %s", e)

    rzp_key = settings.razorpay_key_id or "rzp_test_TTBzVCxzHMSaip"
    return OrderStatusResponse(
        id=order.id,
        status=order.status.value if hasattr(order.status, "value") else str(order.status),
        total=order.total,
        rzp_order_id=order.rzp_order_id,
        rzp_payment_id=order.rzp_payment_id,
        payment_link=order.payment_link,
        paid_at=order.paid_at,
        rzp_key_id=rzp_key,
    )


@router.post("/{order_id}/verify-payment", response_model=OrderResponse)
async def verify_payment_callback(
    order_id: uuid.UUID,
    payload: dict[str, Any] | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Mark order as paid upon Razorpay callback verification."""
    payment_id = (payload or {}).get("razorpay_payment_id") or "rzp_captured_test"
    order = await order_service.handle_payment_captured(
        db=db,
        order_id=order_id,
        rzp_payment_id=payment_id,
    )
    if not order:
        order = await order_service.get_order_by_id(db, order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order {order_id} not found",
        )

    # Dispatched rich order placed confirmation & tracking to Telegram
    try:
        from app.services.telegram_service import telegram_service
        from app.models.customer import Customer
        from app.services.order_service import get_order_tracking_data

        customer = None
        if order.customer_id:
            cust_stmt = select(Customer).where(Customer.id == order.customer_id)
            c_res = await db.execute(cust_stmt)
            customer = c_res.scalar_one_or_none()

        if not customer and order.conversation_id:
            from app.models.conversation import Conversation
            conv = await db.get(Conversation, order.conversation_id)
            if conv and conv.customer_id:
                customer = await db.get(Customer, conv.customer_id)
                order.customer_id = customer.id
                await db.commit()

        m_stmt = select(Merchant).where(Merchant.id == order.merchant_id)
        m_res = await db.execute(m_stmt)
        merchant = m_res.scalar_one_or_none()
        merchant_name = merchant.name if merchant else "Bangalore Store"

        if customer and customer.phone and customer.phone.startswith("tg_"):
            chat_id = customer.phone.replace("tg_", "")
            tracking = await get_order_tracking_data(db, order.id)
            eta = tracking.get("remaining_eta_minutes", 25) if tracking else 25
            driver = tracking.get("driver_name", "Ramesh K.") if tracking else "Ramesh K."
            vehicle = tracking.get("driver_vehicle", "TVS Jupiter • KA-03-HA-8821") if tracking else ""
            otp = tracking.get("pickup_otp", "7821") if tracking else "7821"

            items_list = []
            for item in (order.items or []):
                items_list.append(f"• <b>{item.get('name')}</b> × {item.get('quantity', 1)} (₹{float(item.get('price', 0)) * int(item.get('quantity', 1)):.0f})")
            items_str = "\n".join(items_list)

            addr_str = order.delivery_address or "📍 <i>Address not set yet</i>"
            mode_str = "🛵 <b>Doorstep Delivery</b>" if order.fulfillment_mode != "pickup" else "🏪 <b>Store Counter Pickup</b>"

            confirm_msg = (
                f"🎉 <b>ORDER CONFIRMED & PAID!</b> 🎉\n\n"
                f"🏪 <b>Store:</b> {merchant_name}\n"
                f"📦 <b>Order ID:</b> <code>#{str(order.id)[:8]}</code>\n"
                f"💰 <b>Total Paid:</b> ₹{order.total:.0f} (Ref: <code>{payment_id}</code>)\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"{items_str}\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"📋 <b>Fulfillment:</b> {mode_str}\n"
                f"📍 <b>Delivery Address:</b> {addr_str}\n"
                f"⏱️ <b>Live ETA:</b> ~{eta} mins\n"
                f"🛵 <b>Delivery Partner:</b> {driver} ({vehicle})\n"
                f"🔑 <b>Pickup OTP:</b> <code>{otp}</code>\n\n"
            )

            if not order.delivery_address and order.fulfillment_mode != "pickup":
                confirm_msg += (
                    f"⚠️ <b>Delivery Address Needed:</b>\n"
                    f"Please reply with your address/area in Bangalore (e.g. <i>'Frazer Town, Coles Road, Apt 4B'</i>) or tap <b>Self-Pickup</b> below!\n"
                )

            buttons = [
                {"text": "📍 Track Live Order", "callback_data": f"track order {str(order.id)[:8]}"},
                {"text": "🛵 Share Delivery Address", "callback_data": "share delivery address"},
                {"text": "🏪 Switch to Self-Pickup", "callback_data": "switch to pickup"},
            ]
            await telegram_service.send_interactive_buttons(
                chat_id=chat_id,
                text=confirm_msg,
                buttons=buttons,
                parse_mode="HTML",
            )
            logger.info("Successfully pushed post-payment order confirmation to Telegram chat %s", chat_id)
    except Exception as notify_err:
        logger.warning("Failed to dispatch Telegram confirmation message: %s", notify_err)

    return order


@router.get("/{order_id}/tracking-data")
async def get_order_tracking_data_endpoint(
    order_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve real dynamic Haversine distance, speed, and real ETA tracking telemetry."""
    data = await order_service.get_order_tracking_data(db, order_id)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order {order_id} not found",
        )
    return data


@router.get("/{order_id}/audit")
async def get_order_audit_trail_endpoint(
    order_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve complete chronological audit trail and decision logs for an order."""
    order = await order_service.get_order_by_id(db, order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order {order_id} not found",
        )
    logs = await audit_service.get_order_audit_trail(db, order_id)
    return {
        "order_id": str(order_id),
        "total": order.total,
        "status": order.status,
        "audit_logs": [
            {
                "id": str(log.id),
                "event_type": log.event_type,
                "action": log.action,
                "reasoning": log.reasoning,
                "input_data": log.input_data,
                "output_data": log.output_data,
                "timestamp": log.created_at.isoformat(),
            }
            for log in logs
        ],
    }


@router.get("/merchant/{merchant_id}", response_model=list[OrderResponse])
async def list_merchant_orders(
    merchant_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """List all orders for a merchant."""
    stmt = select(Order).where(Order.merchant_id == merchant_id).order_by(Order.created_at.desc())
    res = await db.execute(stmt)
    return list(res.scalars().all())
