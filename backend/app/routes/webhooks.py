"""Webhook routes — Razorpay and WhatsApp callbacks. (Phase 3-4 implementation)"""

from fastapi import APIRouter

router = APIRouter()


@router.post("/razorpay")
async def razorpay_webhook():
    """Handle Razorpay payment webhooks. (Phase 3)"""
    return {"message": "Razorpay webhook — coming in Phase 3"}


@router.get("/whatsapp")
async def whatsapp_verify():
    """WhatsApp webhook verification challenge. (Phase 4)"""
    return {"message": "WhatsApp verification — coming in Phase 4"}


@router.post("/whatsapp")
async def whatsapp_webhook():
    """Handle incoming WhatsApp messages. (Phase 4)"""
    return {"message": "WhatsApp webhook — coming in Phase 4"}
