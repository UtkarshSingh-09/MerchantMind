"""Exhaustive edge case test suite for 3-Phase Checkout Saga."""

import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.merchant import Merchant
from app.models.product import Product
from app.models.conversation import Conversation
from app.models.order import Order
from app.services.checkout_saga import checkout_saga, CheckoutSagaError


@pytest.mark.asyncio
async def test_saga_multi_item_partial_stock_failure_rolls_back_all(client: AsyncClient, db_session: AsyncSession):
    """If 1 item in a multi-item cart is out of stock, stock for ALL items is preserved."""
    conv_id = uuid.uuid4()
    m = Merchant(name="Bakery Multi", store_address="Indiranagar", email=f"multi_{conv_id.hex[:6]}@bakery.com")
    db_session.add(m)
    await db_session.flush()

    conv = Conversation(id=conv_id, merchant_id=m.id, channel="web", messages=[])
    p1 = Product(merchant_id=m.id, name="Cake", price=500.0, price_paise=50000, stock_quantity=5)
    p2 = Product(merchant_id=m.id, name="Tart", price=200.0, price_paise=20000, stock_quantity=0)
    db_session.add_all([conv, p1, p2])
    await db_session.commit()

    items = [
        {"product_id": str(p1.id), "name": "Cake", "price": 500.0, "quantity": 2},
        {"product_id": str(p2.id), "name": "Tart", "price": 200.0, "quantity": 1},
    ]

    with pytest.raises((CheckoutSagaError, ValueError)) as exc_info:
        await checkout_saga.execute_checkout(
            db=db_session,
            conversation_id=conv_id,
            merchant_id=m.id,
            items=items,
            total=1200.0,
            subtotal=1200.0,
            fulfillment_mode="delivery",
            delivery_address="Indiranagar",
        )

    assert "stock" in str(exc_info.value).lower() or "insufficient" in str(exc_info.value).lower()

    # Verify Product 1 stock was NOT decremented (remains 5)
    await db_session.refresh(p1)
    assert p1.stock_quantity == 5


@pytest.mark.asyncio
async def test_saga_exact_boundary_stock_depletion(client: AsyncClient, db_session: AsyncSession):
    """Ordering exact available stock sets quantity to 0; subsequent order fails."""
    conv_id1 = uuid.uuid4()
    conv_id2 = uuid.uuid4()
    m = Merchant(name="Limited Store", store_address="Koramangala", email=f"lim_{conv_id1.hex[:6]}@store.com")
    db_session.add(m)
    await db_session.flush()

    conv1 = Conversation(id=conv_id1, merchant_id=m.id, channel="web", messages=[])
    conv2 = Conversation(id=conv_id2, merchant_id=m.id, channel="web", messages=[])
    p = Product(merchant_id=m.id, name="Limited Batch Cookies", price=150.0, price_paise=15000, stock_quantity=2)
    db_session.add_all([conv1, conv2, p])
    await db_session.commit()

    # Order 1: Takes all 2 items
    order1 = await checkout_saga.execute_checkout(
        db=db_session,
        conversation_id=conv_id1,
        merchant_id=m.id,
        items=[{"product_id": str(p.id), "name": "Limited Batch Cookies", "price": 150.0, "quantity": 2}],
        total=300.0,
        subtotal=300.0,
        fulfillment_mode="pickup",
    )
    assert order1 is not None

    await db_session.refresh(p)
    assert p.stock_quantity == 0

    # Order 2: Requests 1 item, should fail with stock error
    with pytest.raises((CheckoutSagaError, ValueError)):
        await checkout_saga.execute_checkout(
            db=db_session,
            conversation_id=conv_id2,
            merchant_id=m.id,
            items=[{"product_id": str(p.id), "name": "Limited Batch Cookies", "price": 150.0, "quantity": 1}],
            total=150.0,
            subtotal=150.0,
            fulfillment_mode="pickup",
        )


@pytest.mark.asyncio
async def test_saga_empty_cart_rejection(db_session: AsyncSession):
    """Empty cart raises error before acquiring database locks."""
    conv_id = uuid.uuid4()
    m = Merchant(name="Empty Store", store_address="Whitefield", email=f"empty_{conv_id.hex[:6]}@store.com")
    db_session.add(m)
    await db_session.flush()

    conv = Conversation(id=conv_id, merchant_id=m.id, channel="web", messages=[])
    db_session.add(conv)
    await db_session.commit()

    with pytest.raises((CheckoutSagaError, ValueError)) as exc_info:
        await checkout_saga.execute_checkout(
            db=db_session,
            conversation_id=conv_id,
            merchant_id=m.id,
            items=[],
            total=0.0,
            subtotal=0.0,
            fulfillment_mode="delivery",
        )
    assert "amount" in str(exc_info.value).lower() or "empty" in str(exc_info.value).lower() or "gateway" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_saga_nonexistent_merchant_rejection(db_session: AsyncSession):
    """Invalid merchant UUID raises error."""
    with pytest.raises((CheckoutSagaError, ValueError)):
        await checkout_saga.execute_checkout(
            db=db_session,
            conversation_id=uuid.uuid4(),
            merchant_id=uuid.UUID("00000000-0000-0000-0000-000000000000"),
            items=[{"product_id": "00000000-0000-0000-0000-000000000001", "name": "Item", "price": 100.0, "quantity": 1}],
            total=100.0,
            subtotal=100.0,
            fulfillment_mode="pickup",
        )


@pytest.mark.asyncio
async def test_saga_reentrant_idempotency_does_not_double_decrement_stock(db_session: AsyncSession):
    """Re-submitting the exact same checkout returns cached order and stock is decremented only once."""
    conv_id = uuid.uuid4()
    m = Merchant(name="Idemp Store", store_address="HSR", email=f"idemp_{conv_id.hex[:6]}@store.com")
    db_session.add(m)
    await db_session.flush()

    conv = Conversation(id=conv_id, merchant_id=m.id, channel="web", messages=[])
    p = Product(merchant_id=m.id, name="Idemp Coffee", price=200.0, price_paise=20000, stock_quantity=10)
    db_session.add_all([conv, p])
    await db_session.commit()

    items = [{"product_id": str(p.id), "name": "Idemp Coffee", "price": 200.0, "quantity": 2}]

    # Run 1
    o1 = await checkout_saga.execute_checkout(
        db=db_session,
        conversation_id=conv_id,
        merchant_id=m.id,
        items=items,
        total=400.0,
        subtotal=400.0,
        fulfillment_mode="pickup",
    )

    await db_session.refresh(p)
    assert p.stock_quantity == 8

    # Run 2 with identical conversation and payload
    o2 = await checkout_saga.execute_checkout(
        db=db_session,
        conversation_id=conv_id,
        merchant_id=m.id,
        items=items,
        total=400.0,
        subtotal=400.0,
        fulfillment_mode="pickup",
    )

    assert str(o1.id) == str(o2.id)

    # Stock must remain 8 (not decremented to 6)
    await db_session.refresh(p)
    assert p.stock_quantity == 8


@pytest.mark.asyncio
async def test_saga_authoritative_price_overrides_client_discount_tampering(db_session: AsyncSession):
    """Client tampering with price in payload is ignored; database price is enforced."""
    conv_id = uuid.uuid4()
    m = Merchant(name="Secure Store", store_address="Indiranagar", email=f"sec_{conv_id.hex[:6]}@store.com")
    db_session.add(m)
    await db_session.flush()

    conv = Conversation(id=conv_id, merchant_id=m.id, channel="web", messages=[])
    p = Product(merchant_id=m.id, name="Premium Saffron Cake", price=1200.0, price_paise=120000, stock_quantity=5)
    db_session.add_all([conv, p])
    await db_session.commit()

    # Attacker tries to pass price = 1.00 INR
    hacked_items = [{"product_id": str(p.id), "name": "Premium Saffron Cake", "price": 1.0, "quantity": 1}]

    order = await checkout_saga.execute_checkout(
        db=db_session,
        conversation_id=conv_id,
        merchant_id=m.id,
        items=hacked_items,
        total=1.0,
        subtotal=1.0,
        fulfillment_mode="pickup",
    )

    # Database total must be authoritative 120000 paise (1200.0 INR)
    assert order.total_paise == 120000
    assert order.total == 1200.0
