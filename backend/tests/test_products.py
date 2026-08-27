"""Tests for Product CRUD endpoints and Schema.org catalog export."""

import uuid
import pytest
from httpx import AsyncClient


async def _create_test_merchant(client: AsyncClient) -> str:
    """Helper: create a test merchant and return ID."""
    unique_email = f"merchant_{uuid.uuid4().hex[:8]}@test.com"
    res = await client.post(
        "/api/merchants/",
        json={
            "name": "Sweet Bakes Test",
            "email": unique_email,
            "description": "Bakery catalog testing",
        },
    )
    assert res.status_code == 201
    return res.json()["id"]


@pytest.mark.asyncio
async def test_create_product(client: AsyncClient):
    """POST /api/merchants/{id}/products — should create a product."""
    merchant_id = await _create_test_merchant(client)
    product_data = {
        "name": "Chocolate Cake",
        "description": "Rich chocolate cake with ganache",
        "price": 650.0,
        "category": "Cakes",
        "tags": ["chocolate", "birthday"],
        "in_stock": True,
    }
    response = await client.post(f"/api/merchants/{merchant_id}/products", json=product_data)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == product_data["name"]
    assert data["price"] == product_data["price"]
    assert data["category"] == product_data["category"]
    assert data["in_stock"] is True


@pytest.mark.asyncio
async def test_list_products(client: AsyncClient):
    """GET /api/merchants/{id}/products — should return product list."""
    merchant_id = await _create_test_merchant(client)
    await client.post(
        f"/api/merchants/{merchant_id}/products",
        json={
            "name": "Strawberry Tart",
            "price": 180.0,
            "category": "Pastries",
            "in_stock": True,
        },
    )
    response = await client.get(f"/api/merchants/{merchant_id}/products")
    assert response.status_code == 200
    products = response.json()
    assert isinstance(products, list)
    assert len(products) >= 1


@pytest.mark.asyncio
async def test_list_products_with_filters(client: AsyncClient):
    """GET /api/merchants/{id}/products?category=Cakes — should filter."""
    merchant_id = await _create_test_merchant(client)
    await client.post(
        f"/api/merchants/{merchant_id}/products",
        json={
            "name": "Pineapple Cake",
            "price": 500.0,
            "category": "Cakes",
            "in_stock": True,
        },
    )
    response = await client.get(
        f"/api/merchants/{merchant_id}/products",
        params={"category": "Cakes", "max_price": 600},
    )
    assert response.status_code == 200
    products = response.json()
    for product in products:
        assert product["category"] == "Cakes"
        assert product["price"] <= 600


@pytest.mark.asyncio
async def test_product_for_nonexistent_merchant(client: AsyncClient):
    """POST /api/merchants/{fake_id}/products — should 404."""
    response = await client.post(
        "/api/merchants/00000000-0000-0000-0000-000000000000/products",
        json={"name": "Ghost Item", "price": 100.0},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_catalog_json_ld(client: AsyncClient):
    """GET /api/merchants/{id}/catalog.json — should return Schema.org JSON-LD."""
    merchant_id = await _create_test_merchant(client)
    await client.post(
        f"/api/merchants/{merchant_id}/products",
        json={
            "name": "Truffle Cake",
            "price": 650.0,
            "category": "Cakes",
            "in_stock": True,
        },
    )
    response = await client.get(f"/api/merchants/{merchant_id}/catalog.json")
    assert response.status_code == 200
    data = response.json()

    # Validate Schema.org structure
    assert data["@context"] == "https://schema.org"
    assert data["@type"] == "ItemList"
    assert data["numberOfItems"] >= 1
    assert "itemListElement" in data

    item = data["itemListElement"][0]
    assert item["@type"] == "ListItem"
    assert item["position"] == 1
    assert item["item"]["@type"] == "Product"
    assert item["item"]["name"] == "Truffle Cake"
    assert item["item"]["offers"]["price"] == 650.0
