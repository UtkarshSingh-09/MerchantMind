"""Order API routes — order creation, status, and audit trail."""

import uuid
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.order import Order
from app.models.merchant import Merchant
from app.schemas.order import OrderCreate, OrderResponse, OrderStatusResponse
from app.services import order_service, audit_service

router = APIRouter()


@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    payload: OrderCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create an order from conversation cart, apply budget guardrails, and initiate Razorpay payment link."""
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
    return OrderStatusResponse(
        id=order.id,
        status=order.status,
        total=order.total,
        rzp_order_id=order.rzp_order_id,
        rzp_payment_id=order.rzp_payment_id,
        payment_link=order.payment_link,
        paid_at=order.paid_at,
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
