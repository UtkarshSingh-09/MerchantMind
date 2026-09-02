"""Webhook routes — Razorpay and WhatsApp callbacks."""

import json
import logging
from fastapi import APIRouter, HTTPException, Query, Request, Response, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.services.razorpay_service import razorpay_service
from app.services.whatsapp_service import whatsapp_service
from app.services.whatsapp_session import get_or_create_whatsapp_session
from app.services import order_service
from app.agents.checkout_agent import checkout_agent

logger = logging.getLogger(__name__)

router = APIRouter()


# =========================================================================
# Razorpay Webhook
# =========================================================================

# In-memory webhook event deduplication cache
_PROCESSED_WEBHOOK_EVENTS: set[str] = set()


@router.post("/razorpay")
async def razorpay_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Handle incoming Razorpay payment webhooks with cryptographic HMAC signature verification and idempotency."""
    body_bytes = await request.body()
    body_str = body_bytes.decode("utf-8")
    signature = request.headers.get("X-Razorpay-Signature", "")

    # 1. Verify signature
    is_valid = razorpay_service.verify_webhook_signature(body=body_str, signature=signature)
    if not is_valid:
        logger.warning("Invalid Razorpay webhook signature received.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid webhook signature",
        )

    try:
        payload = json.loads(body_str)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid JSON payload: {exc}")

    event = payload.get("event")
    event_id = payload.get("event_id") or payload.get("id")
    event_payload = payload.get("payload", {})
    payment_entity = event_payload.get("payment", {}).get("entity", {})
    order_entity = event_payload.get("order", {}).get("entity", {})
    payment_link_entity = event_payload.get("payment_link", {}).get("entity", {})

    rzp_payment_id = payment_entity.get("id")
    rzp_order_id = payment_entity.get("order_id") or order_entity.get("id")
    rzp_link_id = payment_link_entity.get("id") or payment_entity.get("notes", {}).get("payment_link_id")
    amount_inr = (payment_entity.get("amount", 0) or 0) / 100.0

    # 2. Idempotent Deduplication by Event ID
    dedup_key = event_id or f"{event}_{rzp_payment_id or rzp_order_id or rzp_link_id}"
    if dedup_key in _PROCESSED_WEBHOOK_EVENTS:
        logger.info("Webhook event %s already processed. Ignoring duplicate delivery.", dedup_key)
        return {"status": "duplicate_ignored", "event_id": dedup_key}

    # Try Redis for multi-instance deduplication
    try:
        import redis.asyncio as aioredis
        redis_client = aioredis.from_url(settings.resolved_redis_url, decode_responses=True)
        is_new = await redis_client.set(f"processed_webhook:{dedup_key}", "1", nx=True, ex=86400)
        await redis_client.aclose()
        if not is_new:
            logger.info("Webhook event %s already in Redis. Ignoring duplicate delivery.", dedup_key)
            return {"status": "duplicate_ignored", "event_id": dedup_key}
    except Exception:
        pass

    _PROCESSED_WEBHOOK_EVENTS.add(dedup_key)

    # 3. Process Webhook Event with DLQ Safety
    try:
        if event in ["payment.captured", "order.paid", "payment_link.paid"]:
            order = await order_service.handle_payment_captured(
                db=db,
                rzp_order_id=rzp_order_id,
                rzp_payment_id=rzp_payment_id,
                rzp_link_id=rzp_link_id,
                amount_paid=amount_inr,
            )
            return {
                "status": "processed",
                "event": event,
                "order_id": str(order.id) if order else None,
                "order_status": order.status if order else "unmatched",
            }

        elif event in ["payment.failed"]:
            error_desc = payment_entity.get("error_description") or "Payment failed"
            order = await order_service.handle_payment_failed(
                db=db,
                rzp_order_id=rzp_order_id,
                rzp_link_id=rzp_link_id,
                error_reason=error_desc,
            )
            return {
                "status": "processed",
                "event": event,
                "order_id": str(order.id) if order else None,
                "order_status": order.status if order else "unmatched",
            }

        return {"status": "ignored", "event": event}

    except Exception as proc_err:
        logger.error("Error processing Razorpay webhook %s: %s", event, proc_err, exc_info=True)
        from app.services.dlq_service import dlq_service
        await dlq_service.record_dead_letter(
            db=db,
            event_type=event or "unknown",
            payload=payload,
            error_message=str(proc_err),
            source="razorpay",
            event_id=event_id,
        )
        return {"status": "recorded_to_dlq", "error": str(proc_err)}



# =========================================================================
# WhatsApp Webhook (Meta Cloud API)
# =========================================================================

@router.get("/whatsapp")
async def whatsapp_verify(
    hub_mode: str | None = Query(None, alias="hub.mode"),
    hub_verify_token: str | None = Query(None, alias="hub.verify_token"),
    hub_challenge: str | None = Query(None, alias="hub.challenge"),
):
    """WhatsApp webhook verification challenge from Meta."""
    logger.info("WhatsApp verification attempt with token: %s", hub_verify_token)
    if hub_mode == "subscribe" and hub_verify_token == settings.whatsapp_verify_token:
        return Response(content=hub_challenge or "", media_type="text/plain")
    raise HTTPException(status_code=403, detail="Verification token mismatch")


@router.post("/whatsapp")
async def whatsapp_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Handle incoming customer WhatsApp messages, invoke agent, and send replies."""
    try:
        data = await request.json()
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON body")

    logger.info("Received WhatsApp webhook payload: %s", data)

    # Process Meta Cloud API webhook structure
    entries = data.get("entry", [])
    for entry in entries:
        changes = entry.get("changes", [])
        for change in changes:
            value = change.get("value", {})
            contacts = value.get("contacts", [])
            messages = value.get("messages", [])

            customer_name = contacts[0].get("profile", {}).get("name") if contacts else None

            for msg in messages:
                msg_id = msg.get("id")
                sender_phone = msg.get("from")
                msg_type = msg.get("type")

                # Extract text content
                message_text = ""
                if msg_type == "text":
                    message_text = msg.get("text", {}).get("body", "").strip()
                elif msg_type == "interactive":
                    interactive = msg.get("interactive", {})
                    if interactive.get("type") == "button_reply":
                        message_text = interactive.get("button_reply", {}).get("title", "")
                    elif interactive.get("type") == "list_reply":
                        message_text = interactive.get("list_reply", {}).get("title", "")

                if not sender_phone or not message_text:
                    continue

                logger.info("Processing WhatsApp message from %s: '%s'", sender_phone, message_text)

                # 1. Mark message as read
                if msg_id:
                    await whatsapp_service.mark_as_read(msg_id)

                try:
                    # 2. Get or create customer session
                    conversation, customer, merchant = await get_or_create_whatsapp_session(
                        db=db,
                        customer_phone=sender_phone,
                        customer_name=customer_name,
                    )

                    # 3. Process with checkout agent
                    agent_res = await checkout_agent.process_message(
                        db=db,
                        merchant=merchant,
                        conversation=conversation,
                        user_message=message_text,
                    )
                    await db.commit()

                    # 4. Send text response back to customer
                    await whatsapp_service.send_text_message(
                        to=sender_phone,
                        text=agent_res.message,
                    )

                    # 5. If checkout was triggered, deliver payment link directly
                    if agent_res.payment_link:
                        await whatsapp_service.send_payment_link_message(
                            to=sender_phone,
                            amount_inr=agent_res.cart_total,
                            payment_link=agent_res.payment_link,
                            merchant_name=merchant.name,
                        )

                except Exception as exc:
                    logger.error("Error processing WhatsApp conversation: %s", exc, exc_info=True)
                    await whatsapp_service.send_text_message(
                        to=sender_phone,
                        text="I'm sorry, I encountered a temporary issue processing your request. Please try again!",
                    )

    return {"status": "success"}


# =========================================================================
# POS / Shopify Inventory Sync Webhook
# =========================================================================

@router.post("/inventory/sync")
async def inventory_sync_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Handle incoming inventory sync webhooks from POS, ERP, or Shopify systems.
    Accepts:
    {
        "merchant_id": "UUID string",
        "source": "shopify | petpooja | pos",
        "updates": [
            {"sku": "optional SKU or id", "name": "Item Name", "in_stock": true, "price": 100, "quantity": 25}
        ]
    }
    """
    from uuid import UUID
    from app.services.inventory_sync_service import inventory_sync_service

    try:
        payload = await request.json()
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid JSON payload: {exc}")

    merchant_id_str = payload.get("merchant_id")
    if not merchant_id_str:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="merchant_id is required")

    try:
        merchant_id = UUID(str(merchant_id_str))
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid merchant_id UUID")

    updates = payload.get("updates", [])
    if not isinstance(updates, list) or len(updates) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="updates must be a non-empty array")

    source = payload.get("source", "pos_webhook")
    result = await inventory_sync_service.sync_batch_inventory(
        db=db,
        merchant_id=merchant_id,
        updates_list=updates,
        source=source,
    )

    if not result.get("success"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=result.get("error"))

    return result

