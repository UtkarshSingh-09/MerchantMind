"""Merchant CRUD routes."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.merchant import Merchant
from app.schemas.merchant import MerchantCreate, MerchantResponse, MerchantUpdate

router = APIRouter()


@router.post("/", response_model=MerchantResponse, status_code=status.HTTP_201_CREATED)
async def create_merchant(data: MerchantCreate, db: AsyncSession = Depends(get_db)):
    """Register a new merchant."""
    # Check for duplicate email
    existing = await db.execute(select(Merchant).where(Merchant.email == data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Merchant with email '{data.email}' already exists",
        )

    from app.middleware.auth import generate_merchant_api_key

    raw_key, key_hash = generate_merchant_api_key()
    merchant_data = data.model_dump()
    merchant = Merchant(**merchant_data, api_key_hash=key_hash)
    db.add(merchant)
    await db.flush()
    await db.refresh(merchant)
    
    response = MerchantResponse.model_validate(merchant)
    response.api_key = raw_key
    return response


@router.get("/", response_model=list[MerchantResponse])
async def list_merchants(db: AsyncSession = Depends(get_db)):
    """List all merchants."""
    result = await db.execute(select(Merchant).order_by(Merchant.created_at.desc()))
    return result.scalars().all()


@router.get("/{merchant_id}", response_model=MerchantResponse)
async def get_merchant(merchant_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Get a specific merchant by ID."""
    result = await db.execute(select(Merchant).where(Merchant.id == merchant_id))
    merchant = result.scalar_one_or_none()
    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Merchant {merchant_id} not found",
        )
    return merchant


@router.put("/{merchant_id}", response_model=MerchantResponse)
async def update_merchant(
    merchant_id: uuid.UUID,
    data: MerchantUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a merchant."""
    result = await db.execute(select(Merchant).where(Merchant.id == merchant_id))
    merchant = result.scalar_one_or_none()
    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Merchant {merchant_id} not found",
        )

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(merchant, field, value)

    await db.flush()
    await db.refresh(merchant)
    return merchant


@router.delete("/{merchant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_merchant(merchant_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Delete a merchant and all associated data."""
    result = await db.execute(select(Merchant).where(Merchant.id == merchant_id))
    merchant = result.scalar_one_or_none()
    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Merchant {merchant_id} not found",
        )

    await db.delete(merchant)
