"""Audit API routes — system decision logs, API call history, and guardrail tracking."""

import uuid
from datetime import datetime
from typing import Any
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services import audit_service

router = APIRouter()


class AuditLogResponse(BaseModel):
    id: uuid.UUID
    merchant_id: uuid.UUID
    order_id: uuid.UUID | None = None
    conversation_id: uuid.UUID | None = None
    event_type: str
    action: str
    reasoning: str
    input_data: dict[str, Any]
    output_data: dict[str, Any]
    created_at: datetime

    model_config = {"from_attributes": True}


@router.get("/order/{order_id}", response_model=list[AuditLogResponse])
async def get_order_audit(
    order_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve full chronological audit trail for a specific order."""
    logs = await audit_service.get_order_audit_trail(db, order_id)
    return logs


@router.get("/conversation/{conversation_id}", response_model=list[AuditLogResponse])
async def get_conversation_audit(
    conversation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve all agent decisions and guardrail checks for a conversation session."""
    logs = await audit_service.get_conversation_audit_trail(db, conversation_id)
    return logs


@router.get("/merchant/{merchant_id}", response_model=list[AuditLogResponse])
async def get_merchant_audit(
    merchant_id: uuid.UUID,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve recent audit logs across all events for a merchant."""
    logs = await audit_service.get_merchant_audit_trail(db, merchant_id, limit=limit)
    return logs
