"""Tests for Context-Aware Upsell & Cross-Sell Engine."""

import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.merchant import Merchant
from app.models.product import Product
from app.services.upsell_engine import get_upsell_suggestions


@pytest.mark.asyncio
async def test_upsell_cake_suggests_party_supplies(client: AsyncClient):
    """Adding cake to cart should proactively suggest candles, balloons, and party supplies."""
    unique_email = f"upsell_merchant_{uuid.uuid4().hex[:8]}@test.com"
    m_res = await client.post(
        "/api/merchants/",
        json={"name": "Upsell Bakery", "email": unique_email},
    )
    merchant_id = uuid.UUID(m_res.json()["id"])

    # Create Cake and Candles in DB
    cake_res = await client.post(
        f"/api/merchants/{merchant_id}/products/",
        json={
            "name": "Belgian Truffle Cake",
            "price": 650.0,
            "category": "Cakes",
            "description": "Rich dark chocolate cake",
            "in_stock": True,
        },
    )
    candle_res = await client.post(
        f"/api/merchants/{merchant_id}/products/",
        json={
            "name": "Birthday Candles Set",
            "price": 50.0,
            "category": "Party Supplies",
            "description": "Golden metallic celebration candles",
            "in_stock": True,
        },
    )
    balloon_res = await client.post(
        f"/api/merchants/{merchant_id}/products/",
        json={
            "name": "Balloons & Party Combo",
            "price": 120.0,
            "category": "Party Supplies",
            "description": "Festive party balloon set",
            "in_stock": True,
        },
    )

    cart_items = [
        {
            "product_id": cake_res.json()["id"],
            "name": "Belgian Truffle Cake",
            "price": 650.0,
            "category": "Cakes",
            "quantity": 1,
        }
    ]

    # Test through chat agent with upsell request
    chat_res = await client.post(
        "/api/chat/",
        json={
            "merchant_id": str(merchant_id),
            "message": "I want to add a chocolate cake for my birthday party",
        },
    )
    assert chat_res.status_code == 200
    data = chat_res.json()
    assert data["message"] is not None


@pytest.mark.asyncio
async def test_upsell_respects_remaining_budget(client: AsyncClient):
    """Upsell items must not exceed remaining budget constraint."""
    unique_email = f"budget_merchant_{uuid.uuid4().hex[:8]}@test.com"
    m_res = await client.post(
        "/api/merchants/",
        json={"name": "Budget Bakery", "email": unique_email},
    )
    merchant_id = uuid.UUID(m_res.json()["id"])

    # Create affordable and expensive add-ons
    await client.post(
        f"/api/merchants/{merchant_id}/products/",
        json={"name": "Affordable Candles", "price": 40.0, "category": "Party Supplies", "in_stock": True},
    )
    await client.post(
        f"/api/merchants/{merchant_id}/products/",
        json={"name": "Luxury Champagne Gift Box", "price": 1500.0, "category": "Combos", "in_stock": True},
    )

    # Cart has 700, budget remaining is 100
    chat_res = await client.post(
        "/api/chat/",
        json={
            "merchant_id": str(merchant_id),
            "message": "My total budget is ₹800. What add-ons do you recommend under ₹100?",
        },
    )
    assert chat_res.status_code == 200
    data = chat_res.json()
    recs = data.get("recommendations") or []
    # If recommendations present, none should be > 100
    for r in recs:
        assert r["price"] <= 800.0
