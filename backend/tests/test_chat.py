"""Tests for Phase 2 Conversational Checkout and Cart endpoints."""

import uuid
import pytest
from httpx import AsyncClient


async def _create_test_merchant_with_products(client: AsyncClient) -> str:
    """Helper: create test merchant and seed test products."""
    email = f"chat_merchant_{uuid.uuid4().hex[:8]}@test.com"
    res = await client.post(
        "/api/merchants/",
        json={
            "name": "Sweet Bakes Test Store",
            "email": email,
            "description": "Bakery testing store",
        },
    )
    assert res.status_code == 201
    merchant_id = res.json()["id"]

    # Add a product
    await client.post(
        f"/api/merchants/{merchant_id}/products",
        json={
            "name": "Chocolate Truffle Cake",
            "price": 650.0,
            "category": "Cakes",
            "description": "Belgian chocolate cake",
            "in_stock": True,
        },
    )
    return merchant_id


@pytest.mark.asyncio
async def test_chat_endpoint_basic(client: AsyncClient):
    """POST /api/chat/ — should process message and return valid response structure."""
    merchant_id = await _create_test_merchant_with_products(client)
    res = await client.post(
        "/api/chat/",
        json={
            "merchant_id": merchant_id,
            "message": "Hello, what items do you have?",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert "conversation_id" in data
    assert "message" in data
    assert isinstance(data["message"], str)
    assert len(data["message"]) > 0


@pytest.mark.asyncio
async def test_get_conversation_history(client: AsyncClient):
    """GET /api/chat/conversations/{id} — should retrieve messages."""
    merchant_id = await _create_test_merchant_with_products(client)
    chat_res = await client.post(
        "/api/chat/",
        json={
            "merchant_id": merchant_id,
            "message": "Tell me about your cakes",
        },
    )
    assert chat_res.status_code == 200
    conv_id = chat_res.json()["conversation_id"]

    history_res = await client.get(f"/api/chat/conversations/{conv_id}")
    assert history_res.status_code == 200
    history_data = history_res.json()
    assert history_data["id"] == conv_id
    assert len(history_data["messages"]) >= 2  # user + assistant


@pytest.mark.asyncio
async def test_get_and_update_cart(client: AsyncClient):
    """GET/POST /api/chat/conversations/{id}/cart — should manage cart state."""
    merchant_id = await _create_test_merchant_with_products(client)
    chat_res = await client.post(
        "/api/chat/",
        json={
            "merchant_id": merchant_id,
            "message": "Start session",
        },
    )
    conv_id = chat_res.json()["conversation_id"]

    # Direct cart update
    dummy_product_id = str(uuid.uuid4())
    update_res = await client.post(
        f"/api/chat/conversations/{conv_id}/cart",
        json={
            "items": [
                {
                    "product_id": dummy_product_id,
                    "name": "Chocolate Truffle Cake",
                    "price": 650.0,
                    "quantity": 2,
                }
            ]
        },
    )
    assert update_res.status_code == 200
    cart_data = update_res.json()
    assert len(cart_data["items"]) == 1
    assert cart_data["total"] == 1300.0

    # Retrieve cart
    get_cart_res = await client.get(f"/api/chat/conversations/{conv_id}/cart")
    assert get_cart_res.status_code == 200
    assert get_cart_res.json()["total"] == 1300.0
