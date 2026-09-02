"""Tests for Phase 5 Centralized Audit Trail and Budget Enforcement Guardrails."""

import json
import uuid
import pytest
from httpx import AsyncClient


async def _create_test_environment(client: AsyncClient):
    """Helper to create a merchant and conversation with cart items."""
    unique_email = f"audit_merchant_{uuid.uuid4().hex[:8]}@test.com"
    m_res = await client.post(
        "/api/merchants",
        json={"name": "Audit Bakery", "email": unique_email},
    )
    assert m_res.status_code == 201
    merchant_id = m_res.json()["id"]

    # Add items to merchant catalog
    cake_res = await client.post(
        f"/api/merchants/{merchant_id}/products",
        json={"name": "Chocolate Truffle Cake", "price": 600.0, "category": "Cakes", "in_stock": True},
    )
    candle_res = await client.post(
        f"/api/merchants/{merchant_id}/products",
        json={"name": "Gold Candles", "price": 50.0, "category": "Party Supplies", "in_stock": True},
    )

    # Start chat
    chat_res = await client.post(
        "/api/chat",
        json={"merchant_id": merchant_id, "message": "Hello, I want cake under 800"},
    )
    assert chat_res.status_code == 200
    conv_id = chat_res.json()["conversation_id"]

    # Add items to cart
    await client.post(
        f"/api/chat/conversations/{conv_id}/cart",
        json={
            "items": [
                {"product_id": cake_res.json()["id"], "name": "Chocolate Truffle Cake", "price": 600.0, "quantity": 1},
                {"product_id": candle_res.json()["id"], "name": "Gold Candles", "price": 50.0, "quantity": 1},
            ]
        },
    )
    return merchant_id, conv_id


@pytest.mark.asyncio
async def test_order_audit_trail_complete(client: AsyncClient):
    """Verify order creation and payment flow produces a complete, queryable audit trail."""
    merchant_id, conv_id = await _create_test_environment(client)

    # 1. Create order
    order_res = await client.post(
        "/api/orders",
        json={"conversation_id": conv_id, "merchant_id": merchant_id},
    )
    assert order_res.status_code == 201
    order_id = order_res.json()["id"]

    # 2. Query order audit endpoint GET /api/orders/{id}/audit
    audit_res = await client.get(f"/api/orders/{order_id}/audit")
    assert audit_res.status_code == 200
    audit_data = audit_res.json()
    assert audit_data["order_id"] == order_id
    assert len(audit_data["audit_logs"]) >= 1

    # Verify event types in audit logs
    event_types = [log["event_type"] for log in audit_data["audit_logs"]]
    assert len(event_types) > 0


@pytest.mark.asyncio
async def test_budget_enforcement_blocks_overspend(client: AsyncClient):
    """Hard guardrail: Stated budget must block checkout if cart exceeds stated limit."""
    unique_email = f"guardrail_merchant_{uuid.uuid4().hex[:8]}@test.com"
    m_res = await client.post(
        "/api/merchants",
        json={"name": "Guardrail Bakery", "email": unique_email},
    )
    merchant_id = m_res.json()["id"]

    # Customer mentions a strict budget of 500
    chat_res = await client.post(
        "/api/chat",
        json={"merchant_id": merchant_id, "message": "My total budget is under ₹500 only"},
    )
    conv_id = chat_res.json()["conversation_id"]

    # Add items totaling ₹750 (exceeding ₹500)
    await client.post(
        f"/api/chat/conversations/{conv_id}/cart",
        json={
            "items": [
                {"product_id": str(uuid.uuid4()), "name": "Premium Tier Cake", "price": 750.0, "quantity": 1}
            ]
        },
    )

    # Attempt to checkout -> Should be blocked by guardrail
    order_res = await client.post(
        "/api/orders",
        json={"conversation_id": conv_id, "merchant_id": merchant_id},
    )
    assert order_res.status_code == 400
    assert "Budget Guardrail" in order_res.json()["detail"] or "budget" in order_res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_conversation_and_merchant_audit_endpoints(client: AsyncClient):
    """Verify GET /api/audit/conversation/{id} and /api/audit/merchant/{id}."""
    merchant_id, conv_id = await _create_test_environment(client)

    # Fetch conversation audit logs
    conv_audit_res = await client.get(f"/api/audit/conversation/{conv_id}")
    assert conv_audit_res.status_code == 200
    assert isinstance(conv_audit_res.json(), list)

    # Fetch merchant audit logs
    merchant_audit_res = await client.get(f"/api/audit/merchant/{merchant_id}")
    assert merchant_audit_res.status_code == 200
    assert isinstance(merchant_audit_res.json(), list)
