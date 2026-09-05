"""Integration tests for Multi-Store Dual-Kitchen Checkout and Payment Synchronization."""

import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.merchant import Merchant
from app.models.product import Product
from app.models.conversation import Conversation
from app.models.order import Order, OrderStatus
from app.schemas.order import MultiOrderCreate
from app.services import order_service


@pytest.mark.asyncio
async def test_multi_order_checkout_decomposition_and_payment(
    client: AsyncClient, db_session: AsyncSession
):
    """Verifies that multi-merchant cart items decompose into distinct kitchen orders,

    are linked as siblings, and payment capture propagates across siblings.
    """
    # 1. Create two separate merchants
    m1 = Merchant(
        name="Taaza Thindi Banashankari Test",
        email=f"taaza_{uuid.uuid4().hex[:6]}@test.com",
        description="Authentic South Indian Filter Coffee and Tiffins",
        is_active=True,
    )
    m2 = Merchant(
        name="Toit Indiranagar Test",
        email=f"toit_{uuid.uuid4().hex[:6]}@test.com",
        description="Wood-Fired Pizza and Brews",
        is_active=True,
    )
    db_session.add_all([m1, m2])
    await db_session.commit()
    await db_session.refresh(m1)
    await db_session.refresh(m2)

    # 2. Create products for each merchant
    coffee = Product(
        merchant_id=m1.id,
        name="Filter Coffee (Degree Coffee)",
        price=25.0,
        category="Beverages",
        in_stock=True,
    )
    pizza = Product(
        merchant_id=m2.id,
        name="Margherita Pizza",
        price=350.0,
        category="Pizza",
        in_stock=True,
    )
    db_session.add_all([coffee, pizza])
    await db_session.commit()
    await db_session.refresh(coffee)
    await db_session.refresh(pizza)

    # 3. Create conversation with cart containing both items
    conv = Conversation(
        channel="web",
        merchant_id=None,
        cart={
            "items": [
                {
                    "product_id": str(coffee.id),
                    "name": coffee.name,
                    "price": coffee.price,
                    "quantity": 1,
                    "merchant_id": str(m1.id),
                    "merchant_name": m1.name,
                },
                {
                    "product_id": str(pizza.id),
                    "name": pizza.name,
                    "price": pizza.price,
                    "quantity": 1,
                    "merchant_id": str(m2.id),
                    "merchant_name": m2.name,
                },
            ],
            "total": 375.0,
            "is_multi_store": True,
        },
        messages=[],
    )
    db_session.add(conv)
    await db_session.commit()
    await db_session.refresh(conv)

    # 4. Invoke multi-order checkout via API
    payload = {
        "conversation_id": str(conv.id),
        "fulfillment_mode": "delivery",
        "delivery_address": "Indiranagar, Bangalore",
        "customer_name": "Utkarsh",
        "customer_phone": "+919876543210",
        "items": conv.cart["items"],
    }
    resp = await client.post("/api/orders/multi-checkout", json=payload)
    assert resp.status_code == 201, resp.text
    data = resp.json()

    # 5. Assert two distinct orders were created with unified total
    assert "primary_order_id" in data
    assert len(data["sibling_order_ids"]) == 1
    assert len(data["orders"]) == 2
    assert data["total"] == 375.0
    assert data["payment_link"] is not None

    primary_id = uuid.UUID(data["primary_order_id"])
    sibling_id = uuid.UUID(data["sibling_order_ids"][0])

    # 6. Verify orders exist in database
    ord1 = await order_service.get_order_by_id(db_session, primary_id)
    ord2 = await order_service.get_order_by_id(db_session, sibling_id)
    assert ord1 is not None
    assert ord2 is not None

    # Check merchant assignment
    assert {ord1.merchant_id, ord2.merchant_id} == {m1.id, m2.id}
    # Check shared unified payment link
    assert ord1.payment_link == ord2.payment_link
    # Check sibling links in audit_trail
    assert ord1.sibling_orders is not None
    assert len(ord1.sibling_orders) == 1
    assert ord1.sibling_orders[0]["order_id"] == str(ord2.id)

    # 7. Simulate payment captured on primary order
    updated_primary = await order_service.handle_payment_captured(
        db=db_session,
        order_id=primary_id,
        rzp_payment_id="pay_test_multi_capture_999",
        amount_paid=375.0,
    )
    await db_session.commit()

    assert updated_primary is not None
    assert updated_primary.status == OrderStatus.PAID

    # 8. Assert sibling order was automatically transitioned to PAID as well!
    await db_session.refresh(ord2)
    assert ord2.status == OrderStatus.PAID
    assert ord2.rzp_payment_id == "pay_test_multi_capture_999"

    # 9. Verify GET /api/orders/{order_id} returns enriched sibling details
    detail_resp = await client.get(f"/api/orders/{primary_id}")
    assert detail_resp.status_code == 200
    detail_data = detail_resp.json()
    assert detail_data["merchant_name"] is not None
    assert len(detail_data["sibling_orders"]) == 1
    assert detail_data["sibling_orders"][0]["status"] == "paid"
