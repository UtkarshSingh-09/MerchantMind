"""Test suite for Merchant API Key Authentication and Multi-Tenant RBAC Isolation."""

import pytest
import uuid
from fastapi import HTTPException, status
from app.models.merchant import Merchant
from app.middleware.auth import (
    hash_api_key,
    generate_merchant_api_key,
    get_authenticated_merchant,
    verify_merchant_access,
)


def test_api_key_generation_and_hashing():
    """Verify cryptographic API key generation and deterministic SHA-256 hashing."""
    raw_key, key_hash = generate_merchant_api_key()
    assert raw_key.startswith("mm_live_")
    assert len(key_hash) == 64
    assert hash_api_key(raw_key) == key_hash


@pytest.mark.asyncio
async def test_auth_missing_header_rejected(db_session):
    """Missing X-Merchant-Key header must raise 401 Unauthorized."""
    with pytest.raises(HTTPException) as exc_info:
        await get_authenticated_merchant(api_key=None, db=db_session)
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "X-Merchant-Key" in exc_info.value.detail


@pytest.mark.asyncio
async def test_auth_invalid_key_rejected(db_session):
    """Invalid X-Merchant-Key must raise 401 Unauthorized."""
    with pytest.raises(HTTPException) as exc_info:
        await get_authenticated_merchant(api_key="mm_live_invalid_key_1234567890", db=db_session)
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Invalid" in exc_info.value.detail


@pytest.mark.asyncio
async def test_auth_valid_key_accepted(db_session):
    """Valid X-Merchant-Key returns authenticated merchant model."""
    raw_key, key_hash = generate_merchant_api_key()
    merchant = Merchant(
        name="Auth Test Bakery",
        email=f"auth_test_{uuid.uuid4().hex[:6]}@example.com",
        api_key_hash=key_hash,
    )
    db_session.add(merchant)
    await db_session.commit()
    await db_session.refresh(merchant)

    authenticated = await get_authenticated_merchant(api_key=raw_key, db=db_session)
    assert authenticated.id == merchant.id
    assert authenticated.name == "Auth Test Bakery"


@pytest.mark.asyncio
async def test_cross_tenant_access_forbidden():
    """Attempting to access another merchant's resource must raise 403 Forbidden."""
    merchant_a = Merchant(id=uuid.uuid4(), name="Store A", email="store_a@example.com")
    target_merchant_id = uuid.uuid4()

    with pytest.raises(HTTPException) as exc_info:
        await verify_merchant_access(
            merchant_id=target_merchant_id,
            auth_merchant=merchant_a,
        )
    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    assert "Access forbidden" in exc_info.value.detail
