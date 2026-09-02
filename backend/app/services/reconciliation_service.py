"""Reconciliation Service — Periodically checks stuck/pending orders directly against Razorpay API."""

import logging
from datetime import datetime, timezone, timedelta
from typing import Any
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.order import Order, OrderStatus
from app.models.product import Product
from app.services.razorpay_service import razorpay_service
from app.services.audit_service import log_audit_event, AuditEventType

logger = logging.getLogger(__name__)


class ReconciliationService:
    """Reconciles orders whose webhooks may have been dropped or delayed."""

    @staticmethod
    async def reconcile_pending_orders(db: AsyncSession, max_age_minutes: int = 60, min_age_minutes: int = 5) -> dict[str, Any]:
        """Scan orders in PAYMENT_LINK_SENT / PENDING older than min_age_minutes and query Razorpay directly."""
        cutoff_min = datetime.now(timezone.utc) - timedelta(minutes=min_age_minutes)
        cutoff_max = datetime.now(timezone.utc) - timedelta(minutes=max_age_minutes)

        stmt = (
            select(Order)
            .where(
                Order.status.in_([OrderStatus.PENDING, OrderStatus.PAYMENT_LINK_SENT]),
                Order.created_at <= cutoff_min,
                Order.created_at >= cutoff_max,
            )
            .limit(50)
        )
        res = await db.execute(stmt)
        orders = list(res.scalars().all())

        reconciled_count = 0
        expired_count = 0
        checked_count = len(orders)
        results: list[dict[str, Any]] = []

        for order in orders:
            try:
                # 1. If we have a Razorpay Payment Link ID, check its status
                if order.rzp_payment_link_id:
                    link_info = razorpay_service.fetch_payment_link(order.rzp_payment_link_id)
                    if hasattr(link_info, "__await__"):
                        link_info = await link_info
                    link_status = link_info.get("status")

                    if link_status == "paid":
                        order.status = OrderStatus.PAID
                        order.paid_at = datetime.now(timezone.utc)
                        order.rzp_payment_id = link_info.get("payment_id")
                        reconciled_count += 1
                        results.append({"order_id": str(order.id), "status": "reconciled_paid", "rzp_status": link_status})
                        
                        await log_audit_event(
                            db=db,
                            event_type=AuditEventType.PAYMENT_CAPTURED,
                            merchant_id=order.merchant_id,
                            order_id=order.id,
                            action="reconciliation_auto_captured",
                            reasoning="Webhook was missed or delayed. Reconciliation job verified payment with Razorpay directly.",
                            output_data={"payment_link_id": order.rzp_payment_link_id, "amount": order.total},
                        )

                    elif link_status in ["expired", "cancelled"]:
                        order.status = OrderStatus.CANCELLED
                        expired_count += 1
                        results.append({"order_id": str(order.id), "status": "reconciled_cancelled", "rzp_status": link_status})
                        
                        # Release reserved inventory
                        for item in (order.items or []):
                            pid = item.get("product_id")
                            qty = item.get("quantity", 1)
                            if pid:
                                stmt_p = select(Product).where(Product.id == pid)
                                res_p = await db.execute(stmt_p)
                                prod = res_p.scalar_one_or_none()
                                if prod and prod.stock_quantity is not None:
                                    prod.stock_quantity += qty
                                    prod.in_stock = True

                # 2. Or check Razorpay Order ID if present
                elif order.rzp_order_id:
                    ord_info = razorpay_service.fetch_order(order.rzp_order_id)
                    if hasattr(ord_info, "__await__"):
                        ord_info = await ord_info
                    ord_status = ord_info.get("status")
                    if ord_status == "paid":
                        order.status = OrderStatus.PAID
                        order.paid_at = datetime.now(timezone.utc)
                        reconciled_count += 1
                        results.append({"order_id": str(order.id), "status": "reconciled_paid", "rzp_status": ord_status})

            except Exception as err:
                logger.warning("Reconciliation check failed for order %s: %s", order.id, err)
                results.append({"order_id": str(order.id), "status": "check_error", "error": str(err)})

        if reconciled_count > 0 or expired_count > 0:
            await db.flush()

        logger.info(
            "Reconciliation complete. Checked: %d, Auto-captured: %d, Expired/Cancelled: %d",
            checked_count,
            reconciled_count,
            expired_count,
        )

        return {
            "checked_count": checked_count,
            "reconciled_paid": reconciled_count,
            "reconciled_cancelled": expired_count,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "details": results,
        }


reconciliation_service = ReconciliationService()
