"""Tests for Phase 3 Razorpay Order creation and Webhook payment events."""

import hmac
import hashlib
import json
import uuid
import pytest
from httpx import AsyncClient

from app.config import settings


async def _create_merchant_with_conversation(client: AsyncClient):
    """Helper to create a merchant and a conversation with items in cart."""
    unique_email = f"order_merchant_{uuid.uuid4().hex[:8]}@test.com"
    m_res = await client.post(
        "/api/merchants",
        json={
            "name": "Sweet Bakes Order Test",
            "email": unique_email,
            "description": "Bakery for testing Razorpay flow",
        },
    )
    assert m_res.status_code == 201
    merchant_id = m_res.json()["id"]

    # Create real products in catalog
    cake_res = await client.post(
        f"/api/merchants/{merchant_id}/products",
        json={"name": "Belgian Chocolate Cake", "price": 750.0, "category": "Cakes", "in_stock": True, "stock_quantity": 10},
    )
    candle_res = await client.post(
        f"/api/merchants/{merchant_id}/products",
        json={"name": "Birthday Candles Set", "price": 50.0, "category": "Party Supplies", "in_stock": True, "stock_quantity": 10},
    )

    # Start chat and populate cart
    chat_res = await client.post(
        "/api/chat",
        json={
            "merchant_id": merchant_id,
            "message": "Start session",
        },
    )
    assert chat_res.status_code == 200
    conv_id = chat_res.json()["conversation_id"]

    # Add items to cart
    await client.post(
        f"/api/chat/conversations/{conv_id}/cart",
        json={
            "items": [
                {
                    "product_id": cake_res.json()["id"],
                    "name": "Belgian Chocolate Cake",
                    "price": 750.0,
                    "quantity": 1,
                },
                {
                    "product_id": candle_res.json()["id"],
                    "name": "Birthday Candles Set",
                    "price": 50.0,
                    "quantity": 1,
                },
            ]
        },
    )
    return merchant_id, conv_id


@pytest.mark.asyncio
async def test_create_order_from_cart(client: AsyncClient):
    """POST /api/orders/ — should create order, compute total, and generate payment link."""
    merchant_id, conv_id = await _create_merchant_with_conversation(client)

    res = await client.post(
        "/api/orders",
        json={
            "conversation_id": conv_id,
            "merchant_id": merchant_id,
            "customer_name": "Test Customer",
            "customer_phone": "+919876543210",
        },
    )
    assert res.status_code == 201
    data = res.json()
    assert "id" in data
    assert data["total"] == 800.0
    assert data["status"] == "payment_link_sent"
    assert data["payment_link"] is not None
    assert len(data["items"]) == 2


@pytest.mark.asyncio
async def test_get_order_and_status(client: AsyncClient):
    """GET /api/orders/{id} and /api/orders/{id}/status — should retrieve order details."""
    merchant_id, conv_id = await _create_merchant_with_conversation(client)

    order_res = await client.post(
        "/api/orders",
        json={
            "conversation_id": conv_id,
            "merchant_id": merchant_id,
        },
    )
    order_id = order_res.json()["id"]

    # Full details
    detail_res = await client.get(f"/api/orders/{order_id}")
    assert detail_res.status_code == 200
    assert detail_res.json()["id"] == order_id
    assert len(detail_res.json()["audit_trail"]) >= 1

    # Lightweight status
    status_res = await client.get(f"/api/orders/{order_id}/status")
    assert status_res.status_code == 200
    assert status_res.json()["status"] == "payment_link_sent"
    assert status_res.json()["total"] == 800.0


@pytest.mark.asyncio
async def test_razorpay_webhook_payment_captured(client: AsyncClient):
    """POST /api/webhooks/razorpay with payment.captured event."""
    merchant_id, conv_id = await _create_merchant_with_conversation(client)

    order_res = await client.post(
        "/api/orders",
        json={
            "conversation_id": conv_id,
            "merchant_id": merchant_id,
        },
    )
    order_data = order_res.json()
    order_id = order_data["id"]
    rzp_order_id = order_data.get("rzp_order_id") or "order_test_12345"

    fake_payment_id = f"pay_{uuid.uuid4().hex[:12]}"
    webhook_payload = {
        "event": "payment.captured",
        "payload": {
            "payment": {
                "entity": {
                    "id": fake_payment_id,
                    "order_id": rzp_order_id,
                    "amount": 80000,
                    "status": "captured",
                }
            }
        },
    }
    raw_body = json.dumps(webhook_payload)
    secret = settings.razorpay_webhook_secret or "your_webhook_secret_here"
    signature = hmac.new(secret.encode("utf-8"), raw_body.encode("utf-8"), hashlib.sha256).hexdigest()

    # Post webhook
    wh_res = await client.post(
        "/api/webhooks/razorpay",
        content=raw_body,
        headers={
            "Content-Type": "application/json",
            "X-Razorpay-Signature": signature,
        },
    )
    assert wh_res.status_code == 200
    assert wh_res.json()["status"] == "processed"

    # Verify order is now marked PAID
    status_res = await client.get(f"/api/orders/{order_id}/status")
    assert status_res.status_code == 200
    assert status_res.json()["status"] == "paid"
    assert status_res.json()["rzp_payment_id"] == fake_payment_id


@pytest.mark.asyncio
async def test_razorpay_webhook_payment_failed(client: AsyncClient):
    """POST /api/webhooks/razorpay with payment.failed event."""
    merchant_id, conv_id = await _create_merchant_with_conversation(client)

    order_res = await client.post(
        "/api/orders",
        json={
            "conversation_id": conv_id,
            "merchant_id": merchant_id,
        },
    )
    order_data = order_res.json()
    order_id = order_data["id"]
    rzp_order_id = order_data.get("rzp_order_id") or "order_test_failed_123"

    webhook_payload = {
        "event": "payment.failed",
        "payload": {
            "payment": {
                "entity": {
                    "id": f"pay_{uuid.uuid4().hex[:12]}",
                    "order_id": rzp_order_id,
                    "error_description": "Card declined by issuer",
                }
            }
        },
    }
    raw_body = json.dumps(webhook_payload)
    secret = settings.razorpay_webhook_secret or "your_webhook_secret_here"
    signature = hmac.new(secret.encode("utf-8"), raw_body.encode("utf-8"), hashlib.sha256).hexdigest()

    wh_res = await client.post(
        "/api/webhooks/razorpay",
        content=raw_body,
        headers={
            "Content-Type": "application/json",
            "X-Razorpay-Signature": signature,
        },
    )
    assert wh_res.status_code == 200

    # Verify status is failed
    status_res = await client.get(f"/api/orders/{order_id}/status")
    assert status_res.status_code == 200
    assert status_res.json()["status"] == "failed"
