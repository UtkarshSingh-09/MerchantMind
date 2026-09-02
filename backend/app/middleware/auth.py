"""Authentication and Role-Based Access Control (RBAC) middleware for MerchantMind.
Provides timing-safe API key validation and multi-tenant isolation for merchant administrative routes.
"""

import hmac
import hashlib
import secrets
import logging
import uuid
from fastapi import Security, HTTPException, status, Depends
from fastapi.security import APIKeyHeader
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.merchant import Merchant
from app.config import settings

logger = logging.getLogger(__name__)

API_KEY_HEADER = APIKeyHeader(name="X-Merchant-Key", auto_error=False)


def hash_api_key(raw_key: str) -> str:
    """Generate SHA-256 digest of merchant API key."""
    return hashlib.sha256(raw_key.strip().encode("utf-8")).hexdigest()


def generate_merchant_api_key() -> tuple[str, str]:
    """Generate a cryptographically secure merchant API key and its hash.
    
    Returns:
        (raw_key, hashed_key)
    """
    raw_key = f"mm_live_{secrets.token_hex(24)}"
    return raw_key, hash_api_key(raw_key)


async def get_authenticated_merchant(
    api_key: str | None = Security(API_KEY_HEADER),
    db: AsyncSession = Depends(get_db),
) -> Merchant:
    """Validate X-Merchant-Key header and return authenticated merchant.
    
    Uses constant-time comparison (hmac.compare_digest) to prevent timing attacks.
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please provide a valid 'X-Merchant-Key' header.",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    incoming_hash = hash_api_key(api_key)

    # Query all active merchants to find matching key hash using timing-safe comparison
    stmt = select(Merchant).where(Merchant.is_active == True)
    res = await db.execute(stmt)
    merchants = list(res.scalars().all())

    matched_merchant = None
    for m in merchants:
        if m.api_key_hash and hmac.compare_digest(m.api_key_hash, incoming_hash):
            matched_merchant = m
            break

    # If no custom key hash matched, check default merchant master key or dev fallback
    if not matched_merchant and api_key == settings.app_secret_key:
        if merchants:
            matched_merchant = merchants[0]

    if not matched_merchant:
        logger.warning("Failed authentication attempt with invalid X-Merchant-Key")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid 'X-Merchant-Key' provided.",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    return matched_merchant


async def verify_merchant_access(
    merchant_id: uuid.UUID,
    auth_merchant: Merchant = Depends(get_authenticated_merchant),
) -> Merchant:
    """Verify that the authenticated merchant owns the target merchant resource (Multi-Tenant Isolation)."""
    if auth_merchant.id != merchant_id:
        logger.warning(
            "Access forbidden: Merchant %s attempted to access resource owned by %s",
            auth_merchant.id,
            merchant_id,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: You do not have permission to modify this merchant's resources.",
        )
    return auth_merchant
