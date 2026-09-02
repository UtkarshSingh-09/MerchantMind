"""Merchant Operations Chat API routes."""

import uuid
from typing import Any
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.merchant import Merchant
from app.models.conversation import Conversation
from app.agents.agent_router import agent_router

router = APIRouter()


class MerchantChatRequest(BaseModel):
    merchant_id: uuid.UUID
    message: str
    conversation_id: uuid.UUID | None = None


class MerchantChatResponse(BaseModel):
    conversation_id: uuid.UUID
    merchant_id: uuid.UUID
    merchant_name: str
    message: str
    action_data: dict[str, Any] | None = None


@router.post("/", response_model=MerchantChatResponse)
async def merchant_chat_endpoint(
    request: MerchantChatRequest,
    db: AsyncSession = Depends(get_db),
):
    """Conversational operations portal for merchants to manage stock, analyze sales, and recover carts."""
    # 1. Fetch merchant
    m_stmt = select(Merchant).where(Merchant.id == request.merchant_id)
    m_res = await db.execute(m_stmt)
    merchant = m_res.scalar_one_or_none()
    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Merchant {request.merchant_id} not found.",
        )

    # 2. Fetch or create console conversation
    conversation: Conversation | None = None
    if request.conversation_id:
        c_stmt = select(Conversation).where(Conversation.id == request.conversation_id)
        c_res = await db.execute(c_stmt)
        conversation = c_res.scalar_one_or_none()

    if not conversation:
        conversation = Conversation(
            id=request.conversation_id or uuid.uuid4(),
            merchant_id=merchant.id,
            channel="merchant_console",
            status="active",
            messages=[],
            cart={},
            agent_reasoning=[],
        )
        db.add(conversation)
        await db.flush()

    # 3. Process message through Multi-Agent Router (MerchantAgent)
    result = await agent_router.route_merchant_message(
        db=db,
        merchant=merchant,
        conversation=conversation,
        user_message=request.message,
    )

    # 4. Save messages to conversation
    messages = list(conversation.messages or [])
    messages.append({
        "role": "user",
        "content": request.message,
    })
    messages.append({
        "role": "assistant",
        "content": result["message"],
        "metadata": result.get("action_data", {}),
    })
    conversation.messages = messages
    await db.commit()

    return MerchantChatResponse(
        conversation_id=conversation.id,
        merchant_id=merchant.id,
        merchant_name=merchant.name,
        message=result["message"],
        action_data=result.get("action_data"),
    )
