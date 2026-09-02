"""
MerchantMind — AI Growth Agent for Razorpay Merchants
FastAPI Application Entry Point
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine, Base
from app.middleware.error_handler import ErrorHandlerMiddleware
from app.routes import merchants, products, chat, orders, webhooks, health, campaigns, audit, merchant_chat, analytics, customers, voice
# Import all models to ensure they register on Base.metadata
from app.models import merchant, product, customer, conversation, order, campaign, audit_log, dead_letter


import asyncio
import logging

logger = logging.getLogger(__name__)


async def background_reconciliation_daemon():
    """Autonomous background worker periodically checking for stuck/pending Razorpay orders."""
    from app.database import async_session
    from app.services.reconciliation_service import reconciliation_service

    logger.info("Autonomous Razorpay reconciliation background worker started (60s tick interval).")
    while True:
        try:
            await asyncio.sleep(60)
            async with async_session() as db:
                res = await reconciliation_service.reconcile_pending_orders(
                    db=db,
                    min_age_minutes=2,
                    max_age_minutes=120,
                )
                if res.get("reconciled_paid", 0) > 0 or res.get("reconciled_cancelled", 0) > 0:
                    logger.info("Autonomous reconciliation cycle completed: %s", res)
        except asyncio.CancelledError:
            logger.info("Autonomous reconciliation worker gracefully stopped.")
            break
        except Exception as exc:
            logger.warning("Reconciliation worker cycle skipped due to transient error: %s", exc)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle — startup and shutdown."""
    # Startup: create tables (dev only — use Alembic in prod)
    from sqlalchemy import text
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(text("ALTER TABLE merchants ADD COLUMN IF NOT EXISTS api_key_hash VARCHAR(64);"))
        await conn.execute(text("ALTER TABLE products ADD COLUMN IF NOT EXISTS price_paise INTEGER;"))
        await conn.execute(text("ALTER TABLE orders ADD COLUMN IF NOT EXISTS total_paise BIGINT;"))
        await conn.execute(text("ALTER TABLE orders ADD COLUMN IF NOT EXISTS subtotal_paise BIGINT;"))
        await conn.execute(text("ALTER TABLE customers ADD COLUMN IF NOT EXISTS saved_addresses JSONB DEFAULT '[]'::jsonb;"))
        await conn.execute(text("ALTER TABLE customers ADD COLUMN IF NOT EXISTS preferences JSONB DEFAULT '{}'::jsonb;"))
        await conn.execute(text("ALTER TABLE customers ADD COLUMN IF NOT EXISTS favorite_merchants JSONB DEFAULT '[]'::jsonb;"))
        # Database-level integrity check constraints
        await conn.execute(text("""
            DO $$ BEGIN 
                IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'check_stock_non_negative') THEN 
                    ALTER TABLE products ADD CONSTRAINT check_stock_non_negative CHECK (stock_quantity IS NULL OR stock_quantity >= 0); 
                END IF; 
                IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'check_price_positive') THEN 
                    ALTER TABLE products ADD CONSTRAINT check_price_positive CHECK (price >= 0); 
                END IF; 
                IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'check_total_positive') THEN 
                    ALTER TABLE orders ADD CONSTRAINT check_total_positive CHECK (total >= 0); 
                END IF; 
            END $$;
        """))

    # Launch background reconciliation daemon
    reconcile_task = asyncio.create_task(background_reconciliation_daemon())

    yield

    # Shutdown: gracefully terminate background tasks and dispose engine
    reconcile_task.cancel()
    try:
        await asyncio.wait_for(asyncio.gather(reconcile_task, return_exceptions=True), timeout=3.0)
    except (asyncio.TimeoutError, Exception):
        pass

    await engine.dispose()


app = FastAPI(
    title="MerchantMind API",
    description=(
        "Multi-Agent Autonomous Commerce Platform for Razorpay Merchants.\n"
        "• Discovery Agent: City-wide store discovery and structured budget guardrails.\n"
        "• Shopping Agent: Conversational checkout, real-time Haversine ETA, and smart upselling.\n"
        "• Merchant Agent: Operational inventory management, sales intelligence, and proactive cart recovery."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# Error handling — structured JSON for unhandled exceptions
app.add_middleware(ErrorHandlerMiddleware)

# CORS — Outermost middleware so all responses (including errors) carry CORS headers
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins if settings.cors_origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(health.router, tags=["Health"])
app.include_router(merchants.router, prefix="/api/merchants", tags=["Merchants"])
app.include_router(products.router, prefix="/api/merchants", tags=["Products"])
app.include_router(chat.router, prefix="/api/chat", tags=["Customer Chat"])
app.include_router(merchant_chat.router, prefix="/api/merchant-chat", tags=["Merchant Agent"])
app.include_router(orders.router, prefix="/api/orders", tags=["Orders"])
app.include_router(webhooks.router, prefix="/api/webhooks", tags=["Webhooks"])
app.include_router(campaigns.router, prefix="/api/campaigns", tags=["Campaigns"])
app.include_router(audit.router, prefix="/api/audit", tags=["Audit"])
app.include_router(customers.router, tags=["Customers"])
app.include_router(voice.router, tags=["Voice AI"])
app.include_router(analytics.router, prefix="/api", tags=["Analytics & Benchmarks"])

