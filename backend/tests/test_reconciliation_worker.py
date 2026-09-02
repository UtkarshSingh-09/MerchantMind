"""Test suite for Autonomous Reconciliation Service and Background Poller."""

import pytest
import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import patch
from app.models.merchant import Merchant
from app.models.product import Product
from app.models.order import Order, OrderStatus
from app.services.reconciliation_service import reconciliation_service


@pytest.mark.asyncio
async def test_reconciliation_auto_captures_paid_order(db_session):
    """Reconciliation poller auto-captures orders paid on Razorpay when webhooks were dropped."""
    merchant = Merchant(name="Recon Test Store", email=f"recon_{uuid.uuid4().hex[:6]}@example.com")
    db_session.add(merchant)
    await db_session.commit()
    await db_session.refresh(merchant)

    order = Order(
        merchant_id=merchant.id,
        items=[{"name": "Chocolate Truffle Cake", "price": 850.0, "quantity": 1}],
        subtotal=850.0,
        total=850.0,
        subtotal_paise=85000,
        total_paise=85000,
        status=OrderStatus.PAYMENT_LINK_SENT,
        rzp_payment_link_id="plink_test_recon_123",
        created_at=datetime.now(timezone.utc) - timedelta(minutes=15),
    )
    db_session.add(order)
    await db_session.commit()
    await db_session.refresh(order)

    # Mock Razorpay API response indicating payment succeeded
    mock_rzp_link = {
        "id": "plink_test_recon_123",
        "status": "paid",
        "payment_id": "pay_test_recon_999",
        "amount_paid": 85000,
    }

    with patch("app.services.razorpay_service.razorpay_service.fetch_payment_link", return_value=mock_rzp_link):
        result = await reconciliation_service.reconcile_pending_orders(
            db=db_session,
            min_age_minutes=5,
            max_age_minutes=60,
        )

    assert result["reconciled_paid"] >= 1
    await db_session.refresh(order)
    assert order.status == OrderStatus.PAID
    assert order.rzp_payment_id == "pay_test_recon_999"
    assert order.paid_at is not None


@pytest.mark.asyncio
async def test_reconciliation_releases_stock_on_expired_order(db_session):
    """Reconciliation poller cancels expired payment links and restores reserved inventory."""
    merchant = Merchant(name="Expiry Test Store", email=f"exp_{uuid.uuid4().hex[:6]}@example.com")
    db_session.add(merchant)
    await db_session.flush()

    product = Product(
        merchant_id=merchant.id,
        name="Artisan Bread",
        price=150.0,
        stock_quantity=5,
        in_stock=True,
    )
    db_session.add(product)
    await db_session.flush()

    order = Order(
        merchant_id=merchant.id,
        items=[{"product_id": str(product.id), "name": "Artisan Bread", "price": 150.0, "quantity": 2}],
        subtotal=300.0,
        total=300.0,
        subtotal_paise=30000,
        total_paise=30000,
        status=OrderStatus.PAYMENT_LINK_SENT,
        rzp_payment_link_id="plink_test_expired_456",
        created_at=datetime.now(timezone.utc) - timedelta(minutes=20),
    )
    db_session.add(order)
    await db_session.commit()

    # Mock Razorpay returning expired link
    mock_expired_link = {
        "id": "plink_test_expired_456",
        "status": "expired",
    }

    with patch("app.services.razorpay_service.razorpay_service.fetch_payment_link", return_value=mock_expired_link):
        result = await reconciliation_service.reconcile_pending_orders(
            db=db_session,
            min_age_minutes=5,
            max_age_minutes=60,
        )

    assert result["reconciled_cancelled"] >= 1
    await db_session.refresh(order)
    await db_session.refresh(product)
    assert order.status == OrderStatus.CANCELLED
    # Stock restored: 5 + 2 = 7
    assert product.stock_quantity == 7
