"""Order routes — create and manage orders. (Phase 3 implementation)"""

from fastapi import APIRouter

router = APIRouter()


@router.post("/")
async def create_order():
    """Create an order from cart and initiate Razorpay payment. (Phase 3)"""
    return {"message": "Orders endpoint — coming in Phase 3"}
