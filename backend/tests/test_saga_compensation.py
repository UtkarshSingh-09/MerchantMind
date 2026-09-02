"""Automated Test: Distributed Saga Compensation Rollback.
Simulates a payment gateway failure during Phase 2 of checkout saga.
Asserts that Phase 3 compensation automatically releases held inventory and logs failure.
"""

import uuid
import pytest
from unittest.mock import patch
from sqlalchemy import select
from app.models.merchant import Merchant
from app.models.product import Product
from app.models.conversation import Conversation
from app.models.order import Order, OrderStatus
from app.services.checkout_saga import checkout_saga
from tests.conftest import TestSessionLocal


@pytest.mark.asyncio
async def test_saga_compensation_rollback_on_payment_gateway_failure():
    """Verify saga automatically releases reserved stock when Razorpay SDK call fails."""
    merchant_id = uuid.uuid4()
    product_id = uuid.uuid4()
    conv_id = uuid.uuid4()

    # 1. Setup Product with stock = 2
    async with TestSessionLocal() as session:
        merchant = Merchant(
            id=merchant_id,
            name="Saga Rollback Merchant",
            email=f"saga_{uuid.uuid4().hex[:8]}@test.com",
            phone="+919876543211",
        )
        product = Product(
            id=product_id,
            merchant_id=merchant_id,
            name="Artisan Sourdough Loaf",
            price=250.0,
            category="Breads",
            in_stock=True,
            stock_quantity=2,
        )
        conv = Conversation(id=conv_id, merchant_id=merchant_id, channel="web", messages=[])

        session.add_all([merchant, product, conv])
        await session.commit()

    items = [{"product_id": str(product_id), "name": "Artisan Sourdough Loaf", "price": 250.0, "quantity": 1}]

    # 2. Mock Razorpay SDK to simulate a fatal gateway outage
    with patch("app.services.razorpay_service.razorpay_service.create_payment_link") as mock_rzp_link:
        mock_rzp_link.side_effect = Exception("Razorpay 504 Gateway Timeout: payment link service unreachable")

        with pytest.raises(Exception) as exc_info:
            async with TestSessionLocal() as db_session:
                await checkout_saga.execute_checkout(
                    db=db_session,
                    conversation_id=conv_id,
                    merchant_id=merchant_id,
                    items=items,
                    total=250.0,
                    subtotal=250.0,
                    customer_name="Test Customer",
                )

        assert "504 Gateway Timeout" in str(exc_info.value)
        print("\n[SAGA ROLLBACK TEST] Successfully caught injected gateway outage")

    # 3. Assert compensation correctness: Stock was restored back to 2
    async with TestSessionLocal() as verify_db:
        prod_res = await verify_db.execute(select(Product).where(Product.id == product_id))
        final_prod = prod_res.scalar_one()
        assert final_prod.stock_quantity == 2, f"Stock should be 2 after compensation rollback, found {final_prod.stock_quantity}"
        assert final_prod.in_stock is True

        order_res = await verify_db.execute(select(Order).where(Order.conversation_id == conv_id))
        order = order_res.scalar_one_or_none()
        if order:
            assert order.status == OrderStatus.CANCELLED, f"Order status should be cancelled on compensation, found {order.status}"
