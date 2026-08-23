"""Chat route — conversational checkout agent. (Phase 2 implementation)"""

from fastapi import APIRouter

router = APIRouter()


@router.post("/")
async def send_message():
    """Send a message to the checkout agent. (Phase 2)"""
    return {"message": "Chat endpoint — coming in Phase 2"}
