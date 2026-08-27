"""Chat routes — Conversational Checkout Agent API."""

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
from app.agents.checkout_agent import checkout_agent

router = APIRouter()


@router.post("/", response_model=ChatResponse)
async def send_chat_message(
    payload: ChatRequest,
    db: AsyncSession = Depends(get_db),
):
    """Send customer message to the checkout agent and receive recommendations & cart actions."""
    # 1. Fetch merchant
    stmt = select(Merchant).where(Merchant.id == payload.merchant_id)
    res = await db.execute(stmt)
    merchant = res.scalar_one_or_none()
    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Merchant {payload.merchant_id} not found",
        )

    # 2. Get or initialize conversation
    try:
        conversation = await get_or_create_conversation(
            db=db,
            merchant_id=payload.merchant_id,
            conversation_id=payload.conversation_id,
            customer_phone=payload.customer_phone,
        )
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    # 3. Process message through Checkout Agent
    chat_response = await checkout_agent.process_message(
        db=db,
        merchant=merchant,
        conversation=conversation,
        user_message=payload.message,
    )

    await db.commit()
    return chat_response


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
