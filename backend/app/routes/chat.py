"""Chat routes — Conversational Checkout Agent API with Discovery Mode."""

import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.merchant import Merchant
from app.models.conversation import Conversation
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ConversationDetailResponse,
    CartUpdatePayload,
)
from app.services.conversation_service import (
    get_or_create_conversation,
    get_conversation_by_id,
    update_conversation_cart,
)
from app.agents.agent_router import agent_router
from app.middleware.rate_limiter import rate_limit

router = APIRouter()


@router.post("/", response_model=ChatResponse, dependencies=[Depends(rate_limit(max_requests=60, window_seconds=60, scope="chat"))])
async def send_chat_message(
    payload: ChatRequest,
    db: AsyncSession = Depends(get_db),
):
    """Send customer message to the multi-agent router.

    If merchant_id is provided → Shopping Agent (single-merchant)
    If merchant_id is None    → Discovery Agent (cross-merchant AI agent)
    """
    merchant = None

    if payload.merchant_id:
        # Shopping Mode: Fetch specific merchant
        stmt = select(Merchant).where(Merchant.id == payload.merchant_id)
        res = await db.execute(stmt)
        merchant = res.scalar_one_or_none()
        if not merchant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Merchant {payload.merchant_id} not found",
            )

    # Get or initialize conversation (merchant_id can be None for Discovery Mode)
    try:
        conversation = await get_or_create_conversation(
            db=db,
            merchant_id=payload.merchant_id,
            conversation_id=payload.conversation_id,
            customer_phone=payload.customer_phone,
            customer_id=payload.customer_id,
        )
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    from app.services.conversation_service import update_conversation_cart
    if payload.cart_items:
        server_cart_items = (conversation.cart or {}).get("items", [])
        if not server_cart_items or len(payload.cart_items) >= len(server_cart_items):
            cart_total = sum(float(it.get("price", 0)) * int(it.get("quantity", 1)) for it in payload.cart_items)
            m_id = payload.cart_items[0].get("merchant_id") if payload.cart_items else None
            update_conversation_cart(
                conversation,
                {
                    "items": payload.cart_items,
                    "total": round(cart_total, 2),
                    "merchant_id": m_id,
                },
            )

    # If conversation already has a locked merchant (from a previous select_store),
    # load that merchant so we continue in Shopping Mode
    if not merchant and conversation.merchant_id:
        stmt = select(Merchant).where(Merchant.id == conversation.merchant_id)
        res = await db.execute(stmt)
        merchant = res.scalar_one_or_none()

    # Route message through Multi-Agent Router (DiscoveryAgent or ShoppingAgent)
    chat_response = await agent_router.route_customer_message(
        db=db,
        merchant=merchant,
        conversation=conversation,
        user_message=payload.message,
    )

    await db.commit()
    return chat_response


@router.post("/stream", dependencies=[Depends(rate_limit(max_requests=60, window_seconds=60, scope="chat_stream"))])
async def send_chat_message_stream(
    payload: ChatRequest,
    db: AsyncSession = Depends(get_db),
):
    """Stream customer message and real-time ReAct reasoning events via Server-Sent Events (SSE)."""
    import json
    import logging
    logger = logging.getLogger(__name__)

    merchant = None

    if payload.merchant_id:
        stmt = select(Merchant).where(Merchant.id == payload.merchant_id)
        res = await db.execute(stmt)
        merchant = res.scalar_one_or_none()
        if not merchant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Merchant {payload.merchant_id} not found",
            )

    try:
        conversation = await get_or_create_conversation(
            db=db,
            merchant_id=payload.merchant_id,
            conversation_id=payload.conversation_id,
            customer_phone=payload.customer_phone,
            customer_id=payload.customer_id,
        )
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    from app.services.conversation_service import update_conversation_cart
    if payload.cart_items:
        server_cart_items = (conversation.cart or {}).get("items", [])
        if not server_cart_items or len(payload.cart_items) >= len(server_cart_items):
            cart_total = sum(float(it.get("price", 0)) * int(it.get("quantity", 1)) for it in payload.cart_items)
            m_id = payload.cart_items[0].get("merchant_id") if payload.cart_items else None
            update_conversation_cart(
                conversation,
                {
                    "items": payload.cart_items,
                    "total": round(cart_total, 2),
                    "merchant_id": m_id,
                },
            )

    if not merchant and conversation.merchant_id:
        stmt = select(Merchant).where(Merchant.id == conversation.merchant_id)
        res = await db.execute(stmt)
        merchant = res.scalar_one_or_none()

    # Ensure conversation row is committed before streaming begins
    await db.commit()
    conv_id = conversation.id
    m_id = merchant.id if merchant else (conversation.merchant_id if conversation else None)

    from app.database import async_session
    from fastapi.responses import StreamingResponse

    async def sse_generator():
        async with async_session() as stream_db:
            try:
                c_stmt = select(Conversation).where(Conversation.id == conv_id)
                c_res = await stream_db.execute(c_stmt)
                stream_conv = c_res.scalar_one_or_none()
                if not stream_conv:
                    return

                stream_merchant = None
                curr_m_id = m_id or stream_conv.merchant_id
                if curr_m_id:
                    m_stmt = select(Merchant).where(Merchant.id == curr_m_id)
                    m_res = await stream_db.execute(m_stmt)
                    stream_merchant = m_res.scalar_one_or_none()

                async for event in agent_router.route_customer_message_streaming(
                    db=stream_db,
                    merchant=stream_merchant,
                    conversation=stream_conv,
                    user_message=payload.message,
                ):
                    yield f"data: {json.dumps(event)}\n\n"
                
                await stream_db.commit()
            except Exception as e:
                logger.error("SSE stream error: %s", e, exc_info=True)
                err_event = {
                    "type": "error",
                    "content": f"Streaming error: {str(e)}",
                }
                yield f"data: {json.dumps(err_event)}\n\n"

    return StreamingResponse(
        sse_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/conversations/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation(
    conversation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve full conversation history, reasoning, and cart state."""
    conversation = await get_conversation_by_id(db, conversation_id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation {conversation_id} not found",
        )
    return conversation


@router.get("/conversations/{conversation_id}/cart")
async def get_conversation_cart(
    conversation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get current cart for a conversation."""
    conversation = await get_conversation_by_id(db, conversation_id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation {conversation_id} not found",
        )
    return conversation.cart or {"items": [], "total": 0.0}


@router.post("/conversations/{conversation_id}/cart")
async def update_cart_directly(
    conversation_id: uuid.UUID,
    payload: CartUpdatePayload,
    db: AsyncSession = Depends(get_db),
):
    """Update cart directly via UI controls."""
    conversation = await get_conversation_by_id(db, conversation_id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation {conversation_id} not found",
        )

    cart_dict = {
        "items": [
            {
                "product_id": str(i.product_id),
                "name": i.name,
                "price": i.price,
                "quantity": i.quantity,
            }
            for i in payload.items
        ]
    }
    update_conversation_cart(conversation, cart_dict)
    await db.commit()
    return conversation.cart
