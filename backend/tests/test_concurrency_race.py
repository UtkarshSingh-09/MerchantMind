"""Automated Test: Real Database Concurrency & Row-Level Locking Race Condition.
Simulates two simultaneous buyers purchasing the last remaining unit (stock = 1) in parallel.
Asserts that exactly one buyer succeeds and the other is cleanly rejected, with zero overselling.
"""

import asyncio
import uuid
import pytest
from sqlalchemy import select
from app.models.merchant import Merchant
from app.models.product import Product
from app.models.conversation import Conversation
from app.models.order import Order, OrderStatus
from app.services.checkout_saga import checkout_saga
from tests.conftest import TestSessionLocal


@pytest.mark.asyncio
async def test_concurrency_row_locking_prevents_overselling():
    """Verify row-level locking (with_for_update) prevents race conditions when 2 users buy the last item."""
    merchant_id = uuid.uuid4()
    product_id = uuid.uuid4()
    conv_id_a = uuid.uuid4()
    conv_id_b = uuid.uuid4()

    # 1. Setup Merchant and Product with EXACTLY 1 item in stock
    async with TestSessionLocal() as session:
        merchant = Merchant(
            id=merchant_id,
            name="Concurrency Bakery",
            email=f"concurrency_{uuid.uuid4().hex[:8]}@test.com",
            phone="+919876543210",
        )
        product = Product(
            id=product_id,
            merchant_id=merchant_id,
            name="Limited Edition Golden Cake",
            price=999.0,
            category="Cakes",
            in_stock=True,
            stock_quantity=1,  # Only 1 left!
        )
        conv_a = Conversation(id=conv_id_a, merchant_id=merchant_id, channel="web", messages=[])
        conv_b = Conversation(id=conv_id_b, merchant_id=merchant_id, channel="web", messages=[])

        session.add_all([merchant, product, conv_a, conv_b])
        await session.commit()

    items = [{"product_id": str(product_id), "name": "Limited Edition Golden Cake", "price": 999.0, "quantity": 1}]

    # 2. Helper to simulate an isolated buyer transaction
    async def simulate_buyer_checkout(buyer_name: str, conv_id: uuid.UUID):
        async with TestSessionLocal() as buyer_db:
            return await checkout_saga.execute_checkout(
                db=buyer_db,
                conversation_id=conv_id,
                merchant_id=merchant_id,
                items=items,
                total=999.0,
                subtotal=999.0,
                customer_name=buyer_name,
            )

    # 3. Fire BOTH checkout requests simultaneously in parallel
    results = await asyncio.gather(
        simulate_buyer_checkout("Buyer A", conv_id_a),
        simulate_buyer_checkout("Buyer B", conv_id_b),
        return_exceptions=True,
    )

    # 4. Assertions: Exactly 1 Success, Exactly 1 Failure
    successes = [r for r in results if isinstance(r, Order)]
    failures = [r for r in results if isinstance(r, Exception)]

    print(f"\n[CONCURRENCY RACE TEST] Total buyers: 2 | Successes: {len(successes)} | Failures: {len(failures)}")

    assert len(successes) == 1, "Expected exactly one buyer to win the race for the last item"
    assert len(failures) == 1, "Expected exactly one buyer to be rejected due to out of stock"

    winning_order = successes[0]
    assert winning_order.status == OrderStatus.PAYMENT_LINK_SENT
    assert winning_order.payment_link is not None

    rejected_error = failures[0]
    assert "out of stock" in str(rejected_error).lower() or "insufficient stock" in str(rejected_error).lower()

    # 5. Verify final database state: Stock must be exactly 0, in_stock False, exactly 1 Order in DB
    async with TestSessionLocal() as verify_db:
        prod_res = await verify_db.execute(select(Product).where(Product.id == product_id))
        final_prod = prod_res.scalar_one()
        assert final_prod.stock_quantity == 0, f"Stock quantity must be 0, found {final_prod.stock_quantity}"
        assert final_prod.in_stock is False

        orders_res = await verify_db.execute(select(Order).where(Order.merchant_id == merchant_id))
        all_orders = list(orders_res.scalars().all())
        assert len(all_orders) == 1, f"Expected 1 order in database, found {len(all_orders)}"
