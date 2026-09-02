"""Customer profile and memory management routes."""

import uuid
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.customer import Customer
from app.models.merchant import Merchant
from app.services.memory_service import build_customer_profile_memory

router = APIRouter(prefix="/api/customers", tags=["customers"])


@router.get("/demo")
async def get_or_create_demo_customer(db: AsyncSession = Depends(get_db)):
    """Fetch or dynamically create the primary demo customer with full memory context."""
    # Find any existing merchant to link to
    stmt_m = select(Merchant).limit(1)
    res_m = await db.execute(stmt_m)
    merchant = res_m.scalar_one_or_none()
    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No merchants found. Please run seed script first.",
        )

    # Check for demo customer
    stmt_c = select(Customer).where(Customer.phone == "+919876543210").limit(1)
    res_c = await db.execute(stmt_c)
    customer = res_c.scalars().first()

    saved_addrs = [
        {
            "label": "Home",
            "address": "Flat 402, 100 Feet Road, Indiranagar, Bangalore - 560038",
            "lat": 12.9784,
            "lng": 77.6408,
            "is_default": True,
        },
        {
            "label": "Office",
            "address": "WeWork Galaxy, Residency Road, Shanthala Nagar, Bangalore - 560025",
            "lat": 12.9716,
            "lng": 77.5946,
            "is_default": False,
        },
    ]
    prefs = {
        "dietary": ["Vegetarian"],
        "preferred_spice": "Medium",
        "max_typical_budget": 500,
        "favorite_cuisines": ["Chinese", "Artisan Bakery", "Specialty Coffee"],
    }
    favs = [
        {
            "name": "Beijing Bites",
            "last_item": "Veg Manchurian",
            "rating": 5,
            "order_count": 2,
        },
        {
            "name": "Sweet Chariot",
            "last_item": "Belgian Chocolate Truffle Cake",
            "rating": 5,
            "order_count": 2,
        },
    ]

    if not customer:
        customer = Customer(
            id=uuid.uuid4(),
            merchant_id=merchant.id,
            name="Utkarsh Singh",
            phone="+919876543210",
            email="utkarsh@merchantmind.ai",
            total_spent=1420.0,
            order_count=4,
            saved_addresses=saved_addrs,
            preferences=prefs,
            favorite_merchants=favs,
        )
        db.add(customer)
    else:
        customer.name = "Utkarsh Singh"
        customer.saved_addresses = saved_addrs
        customer.preferences = prefs
        customer.favorite_merchants = favs

    await db.commit()
    await db.refresh(customer)

    memory_summary = await build_customer_profile_memory(customer.id, db)

    return {
        "id": str(customer.id),
        "name": customer.name,
        "phone": customer.phone,
        "email": customer.email,
        "saved_addresses": customer.saved_addresses,
        "preferences": customer.preferences,
        "favorite_merchants": customer.favorite_merchants,
        "order_count": customer.order_count,
        "total_spent": customer.total_spent,
        "formatted_memory": memory_summary,
    }


@router.get("/{customer_id}")
async def get_customer_profile(customer_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Fetch customer details and saved locations."""
    stmt = select(Customer).where(Customer.id == customer_id)
    res = await db.execute(stmt)
    customer = res.scalar_one_or_none()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer {customer_id} not found",
        )

    memory_summary = await build_customer_profile_memory(customer.id, db)

    return {
        "id": str(customer.id),
        "name": customer.name,
        "phone": customer.phone,
        "email": customer.email,
        "saved_addresses": customer.saved_addresses or [],
        "preferences": customer.preferences or {},
        "favorite_merchants": customer.favorite_merchants or [],
        "order_count": customer.order_count,
        "total_spent": customer.total_spent,
        "formatted_memory": memory_summary,
    }
