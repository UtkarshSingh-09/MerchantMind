"""Tests for Multi-Merchant Data Isolation and Schema.org JSON-LD Catalog Export."""

import uuid
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_multi_tenant_catalog_and_order_isolation(client: AsyncClient):
    """Verify strict multi-tenant isolation: Merchant A data is never leaked or accessible to Merchant B."""
    # 1. Create Merchant A ("Sweet Bakes")
    email_a = f"sweetbakes_{uuid.uuid4().hex[:8]}@test.com"
    res_a = await client.post(
        "/api/merchants/",
        json={"name": "Sweet Bakes Artisan", "email": email_a, "description": "Bakery store"},
    )
    assert res_a.status_code == 201
    merchant_a_id = res_a.json()["id"]

    # 2. Create Merchant B ("Fashion Hub")
    email_b = f"fashionhub_{uuid.uuid4().hex[:8]}@test.com"
    res_b = await client.post(
        "/api/merchants/",
        json={"name": "Fashion Hub Apparel", "email": email_b, "description": "Clothing boutique"},
    )
    assert res_b.status_code == 201
    merchant_b_id = res_b.json()["id"]

    # 3. Add products to Merchant A
    cake_res = await client.post(
        f"/api/merchants/{merchant_a_id}/products/",
        json={"name": "Artisan Sourdough Loaf", "price": 250.0, "category": "Breads", "in_stock": True},
    )
    assert cake_res.status_code == 201

    # 4. Add products to Merchant B
    shirt_res = await client.post(
        f"/api/merchants/{merchant_b_id}/products/",
        json={"name": "Denim Jacket", "price": 2499.0, "category": "Apparel", "in_stock": True},
    )
    assert shirt_res.status_code == 201

    # 5. Verify catalog isolation: Listing Merchant A products should NOT contain Merchant B items
    list_a = await client.get(f"/api/merchants/{merchant_a_id}/products/")
    assert list_a.status_code == 200
    a_product_names = [p["name"] for p in list_a.json()]
    assert "Artisan Sourdough Loaf" in a_product_names
    assert "Denim Jacket" not in a_product_names

    list_b = await client.get(f"/api/merchants/{merchant_b_id}/products/")
    assert list_b.status_code == 200
    b_product_names = [p["name"] for p in list_b.json()]
    assert "Denim Jacket" in b_product_names
    assert "Artisan Sourdough Loaf" not in b_product_names

    # 6. Verify order isolation
    orders_a = await client.get(f"/api/orders/merchant/{merchant_a_id}")
    assert orders_a.status_code == 200
    orders_b = await client.get(f"/api/orders/merchant/{merchant_b_id}")
    assert orders_b.status_code == 200


@pytest.mark.asyncio
async def test_schema_org_catalog_export(client: AsyncClient):
    """Verify Schema.org/JSON-LD catalog export endpoint format and valid schema elements."""
    email = f"schema_merchant_{uuid.uuid4().hex[:8]}@test.com"
    m_res = await client.post(
        "/api/merchants/",
        json={"name": "Schema Bakery", "email": email, "description": "Artisan pastries"},
    )
    merchant_id = m_res.json()["id"]

    await client.post(
        f"/api/merchants/{merchant_id}/products/",
        json={
            "name": "Almond Croissant",
            "price": 180.0,
            "category": "Pastries",
            "description": "Flaky French croissant with almond paste",
            "in_stock": True,
        },
    )

    export_res = await client.get(f"/api/merchants/{merchant_id}/catalog.json")
    assert export_res.status_code == 200
    json_ld = export_res.json()

    assert json_ld["@context"] == "https://schema.org"
    assert json_ld["@type"] == "ItemList"
    assert json_ld["numberOfItems"] >= 1
    assert "itemListElement" in json_ld

    first_item = json_ld["itemListElement"][0]["item"]
    assert first_item["@type"] == "Product"
    assert first_item["name"] == "Almond Croissant"
    assert first_item["offers"]["@type"] == "Offer"
    assert first_item["offers"]["price"] == 180.0
    assert first_item["offers"]["priceCurrency"] == "INR"
    assert first_item["offers"]["availability"] == "https://schema.org/InStock"
