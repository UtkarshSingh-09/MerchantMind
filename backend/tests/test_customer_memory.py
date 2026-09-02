"""Automated Test Suite for Ambient Customer Memory & Profile Context Injection."""

import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.customer import Customer
from app.models.merchant import Merchant
from app.models.order import Order, OrderStatus
from app.services.memory_service import build_customer_profile_memory


@pytest.mark.asyncio
async def test_demo_customer_endpoint_returns_memory_profile(client: AsyncClient, db_session: AsyncSession):
    """GET /api/customers/demo creates and returns demo customer with full memory context."""
    # Ensure a merchant exists
    m = Merchant(name="Demo City Merchant", store_address="Indiranagar, Bangalore", email=f"city_{uuid.uuid4().hex[:6]}@demo.com")
    db_session.add(m)
    await db_session.commit()

    resp = await client.get("/api/customers/demo")
    assert resp.status_code == 200
    data = resp.json()

    assert data["name"] == "Utkarsh Singh"
    assert data["phone"] == "+919876543210"
    assert len(data["saved_addresses"]) >= 1
    assert data["saved_addresses"][0]["label"] == "Home"
    assert "formatted_memory" in data
    assert "Indiranagar" in data["formatted_memory"]
    assert "Vegetarian" in data["formatted_memory"]
    assert "Beijing Bites" in data["formatted_memory"]


@pytest.mark.asyncio
async def test_customer_profile_memory_saved_addresses_recall(db_session: AsyncSession):
    """Saved delivery locations are formatted cleanly with default tags."""
    cust_id = uuid.uuid4()
    m_id = uuid.uuid4()

    m = Merchant(id=m_id, name="Address Bakery", store_address="Koramangala", email=f"addr_{cust_id.hex[:6]}@store.com")
    db_session.add(m)
    await db_session.flush()

    c = Customer(
        id=cust_id,
        merchant_id=m_id,
        name="Rohan Verma",
        phone="+919812345678",
        saved_addresses=[
            {"label": "Home", "address": "Penthouse 12, Koramangala 4th Block", "lat": 12.9352, "lng": 77.6245, "is_default": True},
            {"label": "Office", "address": "Bagmane Tech Park, CV Raman Nagar", "lat": 12.9866, "lng": 77.6582, "is_default": False},
        ],
    )
    db_session.add(c)
    await db_session.commit()

    memory_prompt = await build_customer_profile_memory(cust_id, db_session)
    assert "Rohan Verma" in memory_prompt
    assert "Home [DEFAULT]: Penthouse 12, Koramangala 4th Block" in memory_prompt
    assert "Office: Bagmane Tech Park" in memory_prompt


@pytest.mark.asyncio
async def test_customer_profile_memory_preferences_injection(db_session: AsyncSession):
    """Dietary and spice preferences are clearly emitted for agent consumption."""
    cust_id = uuid.uuid4()
    m_id = uuid.uuid4()

    m = Merchant(id=m_id, name="Spice Kitchen", store_address="HSR Layout", email=f"spice_{cust_id.hex[:6]}@store.com")
    db_session.add(m)
    await db_session.flush()

    c = Customer(
        id=cust_id,
        merchant_id=m_id,
        name="Priya Sharma",
        phone="+919876500001",
        preferences={
            "dietary": ["Vegan", "Gluten-Free"],
            "preferred_spice": "Mild",
            "max_typical_budget": 800,
        },
    )
    db_session.add(c)
    await db_session.commit()

    memory_prompt = await build_customer_profile_memory(cust_id, db_session)
    assert "Vegan, Gluten-Free" in memory_prompt
    assert "Spice: Mild" in memory_prompt
    assert "Typical Budget: ₹800" in memory_prompt


@pytest.mark.asyncio
async def test_customer_profile_memory_favorite_merchants_and_ratings(db_session: AsyncSession):
    """Past ratings and favorite merchants are explicitly surfaced to the agent."""
    cust_id = uuid.uuid4()
    m_id = uuid.uuid4()

    m = Merchant(id=m_id, name="Ratings Merchant", store_address="Whitefield", email=f"rate_{cust_id.hex[:6]}@store.com")
    db_session.add(m)
    await db_session.flush()

    c = Customer(
        id=cust_id,
        merchant_id=m_id,
        name="Ananya Roy",
        phone="+919876500002",
        favorite_merchants=[
            {"name": "Glen's Bakehouse", "last_item": "Red Velvet Cupcake", "rating": 5},
            {"name": "Meghana Foods", "last_item": "Special Biryani", "rating": 5},
        ],
    )
    db_session.add(c)
    await db_session.commit()

    memory_prompt = await build_customer_profile_memory(cust_id, db_session)
    assert "Glen's Bakehouse (Rated 5/5 ⭐ — Loved 'Red Velvet Cupcake')" in memory_prompt
    assert "Meghana Foods" in memory_prompt


@pytest.mark.asyncio
async def test_customer_profile_memory_null_safety(db_session: AsyncSession):
    """Null customer ID or non-existent customer safely returns empty string without crashing."""
    mem_none = await build_customer_profile_memory(None, db_session)
    assert mem_none == ""

    mem_missing = await build_customer_profile_memory(uuid.uuid4(), db_session)
    assert mem_missing == ""


@pytest.mark.asyncio
async def test_chat_endpoint_with_customer_id_memory_integration(client: AsyncClient, db_session: AsyncSession):
    """Chat endpoint accepts customer_id and executes multi-agent conversation with memory."""
    m_id = uuid.uuid4()
    m = Merchant(id=m_id, name="Beijing Bites Indiranagar", store_address="Indiranagar", email=f"bb_{m_id.hex[:6]}@bites.com")
    db_session.add(m)
    await db_session.flush()

    cust_id = uuid.uuid4()
    c = Customer(
        id=cust_id,
        merchant_id=m_id,
        name="Utkarsh Singh",
        phone="+919876543210",
        saved_addresses=[{"label": "Home", "address": "Indiranagar", "is_default": True}],
    )
    db_session.add(c)
    await db_session.commit()

    resp = await client.post(
        "/api/chat",
        json={
            "customer_id": str(cust_id),
            "message": "Hey please order me one Manchurian under 500",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "conversation_id" in data
    assert "message" in data
    assert len(data["message"]) > 0
