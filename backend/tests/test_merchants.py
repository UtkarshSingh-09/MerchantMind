"""Tests for Merchant CRUD endpoints."""

import uuid
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_merchant(client: AsyncClient):
    """POST /api/merchants — should create a merchant."""
    unique_email = f"bakery_{uuid.uuid4().hex[:8]}@test.com"
    payload = {
        "name": "Test Bakery",
        "email": unique_email,
        "phone": "+919999999999",
        "description": "A test bakery for unit tests",
    }
    response = await client.post("/api/merchants/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == payload["name"]
    assert data["email"] == unique_email
    assert data["is_active"] is True
    assert "id" in data


@pytest.mark.asyncio
async def test_create_merchant_invalid_email(client: AsyncClient):
    """POST /api/merchants with invalid email — should 422."""
    payload = {
        "name": "Test Bakery",
        "email": "not-a-valid-email",
        "phone": "+919999999999",
    }
    response = await client.post("/api/merchants/", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_merchants(client: AsyncClient):
    """GET /api/merchants — should return list."""
    response = await client.get("/api/merchants/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_get_merchant_not_found(client: AsyncClient):
    """GET /api/merchants/{id} with fake UUID — should 404."""
    response = await client.get("/api/merchants/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_merchant_not_found(client: AsyncClient):
    """DELETE /api/merchants/{id} with fake UUID — should 404."""
    response = await client.delete("/api/merchants/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
