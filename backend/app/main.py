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
from app.routes import merchants, products, chat, orders, webhooks, health, campaigns, audit
# Import all models to ensure they register on Base.metadata
from app.models import merchant, product, customer, conversation, order, campaign, audit_log


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle — startup and shutdown."""
    # Startup: create tables (dev only — use Alembic in prod)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown: dispose engine
    await engine.dispose()


app = FastAPI(
    title="MerchantMind API",
    description=(
        "AI-powered growth agent for Razorpay merchants. "
        "Conversational checkout, intelligent upselling, campaign orchestration."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Error handling — structured JSON for unhandled exceptions
app.add_middleware(ErrorHandlerMiddleware)

# Register routes
app.include_router(health.router, tags=["Health"])
app.include_router(merchants.router, prefix="/api/merchants", tags=["Merchants"])
app.include_router(products.router, prefix="/api/merchants", tags=["Products"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(orders.router, prefix="/api/orders", tags=["Orders"])
app.include_router(webhooks.router, prefix="/api/webhooks", tags=["Webhooks"])
app.include_router(campaigns.router, prefix="/api/campaigns", tags=["Campaigns"])
app.include_router(audit.router, prefix="/api/audit", tags=["Audit"])
