"""Analytics and Evaluation Benchmark routes."""

import logging
from typing import Any
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services.eval_harness import eval_harness
from app.services.reconciliation_service import reconciliation_service
from app.services.dlq_service import dlq_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["Analytics & Benchmarks"])


@router.get("/benchmarks")
async def get_evaluation_benchmarks() -> dict[str, Any]:
    """Execute the 35-case agentic benchmark suite and return live metrics."""
    return await eval_harness.run_benchmark()


@router.post("/reconciliation/run")
async def run_reconciliation(
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Manually trigger background reconciliation for stuck orders."""
    return await reconciliation_service.reconcile_pending_orders(db)


@router.get("/dlq")
async def get_dead_letter_queue(
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """Retrieve dead letter queue webhook events."""
    entries = await dlq_service.get_pending_dead_letters(db, limit=limit)
    return [
        {
            "id": str(e.id),
            "event_type": e.event_type,
            "source": e.source,
            "error_message": e.error_message,
            "retry_count": e.retry_count,
            "status": e.status,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        }
        for e in entries
    ]
