"""Health check endpoint."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check — verifies the API is running."""
    return {
        "status": "healthy",
        "service": "MerchantMind API",
        "version": "1.0.0",
    }
