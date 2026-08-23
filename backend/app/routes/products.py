"""Product CRUD routes + Schema.org catalog export."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.merchant import Merchant
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductResponse, ProductUpdate

router = APIRouter()


async def _get_merchant(merchant_id: uuid.UUID, db: AsyncSession) -> Merchant:
    """Helper: fetch merchant or 404."""
    result = await db.execute(select(Merchant).where(Merchant.id == merchant_id))
    merchant = result.scalar_one_or_none()
    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Merchant {merchant_id} not found",
        )
    return merchant


@router.post(
    "/{merchant_id}/products",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_product(
    merchant_id: uuid.UUID,
    data: ProductCreate,
    db: AsyncSession = Depends(get_db),
):
    """Add a product to a merchant's catalog."""
    await _get_merchant(merchant_id, db)

    product = Product(merchant_id=merchant_id, **data.model_dump())
    # Auto-generate Schema.org JSON-LD
    product.schema_json = product.to_schema_org()

    db.add(product)
    await db.flush()
    await db.refresh(product)
    return product


@router.get("/{merchant_id}/products", response_model=list[ProductResponse])
async def list_products(
    merchant_id: uuid.UUID,
    category: str | None = None,
    in_stock: bool | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    search: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """List products in a merchant's catalog with optional filters."""
    await _get_merchant(merchant_id, db)

    query = select(Product).where(Product.merchant_id == merchant_id)

    if category:
        query = query.where(Product.category == category)
    if in_stock is not None:
        query = query.where(Product.in_stock == in_stock)
    if min_price is not None:
        query = query.where(Product.price >= min_price)
    if max_price is not None:
        query = query.where(Product.price <= max_price)
    if search:
        query = query.where(
            Product.name.ilike(f"%{search}%") | Product.description.ilike(f"%{search}%")
        )

    query = query.order_by(Product.category, Product.name)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{merchant_id}/products/{product_id}", response_model=ProductResponse)
async def get_product(
    merchant_id: uuid.UUID,
    product_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific product."""
    result = await db.execute(
        select(Product).where(
            Product.id == product_id, Product.merchant_id == merchant_id
        )
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product {product_id} not found",
        )
    return product


@router.put("/{merchant_id}/products/{product_id}", response_model=ProductResponse)
async def update_product(
    merchant_id: uuid.UUID,
    product_id: uuid.UUID,
    data: ProductUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a product."""
    result = await db.execute(
        select(Product).where(
            Product.id == product_id, Product.merchant_id == merchant_id
        )
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product {product_id} not found",
        )

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)

    # Regenerate Schema.org JSON-LD
    product.schema_json = product.to_schema_org()

    await db.flush()
    await db.refresh(product)
    return product


@router.delete(
    "/{merchant_id}/products/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_product(
    merchant_id: uuid.UUID,
    product_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Delete a product from the catalog."""
    result = await db.execute(
        select(Product).where(
            Product.id == product_id, Product.merchant_id == merchant_id
        )
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product {product_id} not found",
        )

    await db.delete(product)


@router.get("/{merchant_id}/catalog.json")
async def get_catalog_json_ld(
    merchant_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Export merchant's catalog as Schema.org/JSON-LD — agent-readable format."""
    merchant = await _get_merchant(merchant_id, db)

    result = await db.execute(
        select(Product)
        .where(Product.merchant_id == merchant_id, Product.in_stock == True)
        .order_by(Product.category, Product.name)
    )
    products = result.scalars().all()

    return {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": f"{merchant.name} — Product Catalog",
        "description": merchant.description or f"Products from {merchant.name}",
        "numberOfItems": len(products),
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": i + 1,
                "item": product.to_schema_org(),
            }
            for i, product in enumerate(products)
        ],
    }
