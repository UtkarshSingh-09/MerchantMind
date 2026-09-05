"""Agent Router — Multi-Agent Orchestrator for MerchantMind.
Routes incoming conversation requests to:
- DiscoveryAgent: When customer is exploring without a pre-selected store
- ShoppingAgent: When customer is locked into a specific merchant storefront
- MerchantAgent: When store manager is executing operations, stock management, or sales queries
"""

import logging
from typing import Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.merchant import Merchant
from app.models.conversation import Conversation
from app.agents.discovery_agent import discovery_agent, DiscoveryAgent
from app.agents.shopping_agent import shopping_agent, ShoppingAgent
from app.agents.merchant_agent import merchant_agent, MerchantAgent
from app.schemas.chat import ChatResponse

logger = logging.getLogger(__name__)


class AgentRouter:
    """Central multi-agent orchestrator and request router."""

    def __init__(self):
        self.discovery_agent: DiscoveryAgent = discovery_agent
        self.shopping_agent: ShoppingAgent = shopping_agent
        self.merchant_agent: MerchantAgent = merchant_agent

    async def _resolve_merchant(
        self,
        db: AsyncSession,
        merchant: Merchant | None,
        conversation: Conversation,
    ) -> Merchant | None:
        """Resolve active merchant from conversation or cart items if not explicitly provided."""
        if merchant is not None:
            return merchant
        if conversation.merchant_id:
            m_stmt = select(Merchant).where(Merchant.id == conversation.merchant_id)
            m_res = await db.execute(m_stmt)
            found = m_res.scalar_one_or_none()
            if found:
                return found
        if conversation.cart and conversation.cart.get("items"):
            import uuid
            from app.models.product import Product
            for it in conversation.cart["items"]:
                pid = it.get("product_id")
                if pid:
                    try:
                        p_uuid = uuid.UUID(str(pid))
                        p_stmt = select(Product).where(Product.id == p_uuid)
                        p_res = await db.execute(p_stmt)
                        prod = p_res.scalar_one_or_none()
                        if prod and prod.merchant_id:
                            m_stmt = select(Merchant).where(Merchant.id == prod.merchant_id)
                            m_res = await db.execute(m_stmt)
                            matched = m_res.scalar_one_or_none()
                            if matched:
                                conversation.merchant_id = matched.id
                                return matched
                    except Exception as err:
                        logger.warning("Failed resolving product merchant: %s", err)
        return None

    def classify_routing_intent(
        self,
        user_message: str,
        current_merchant: Merchant | None = None,
        cart: dict | None = None,
    ) -> dict[str, Any]:
        """Determine routing target and confidence score based on explicit message intent and session context."""
        msg_lower = (user_message or "").lower()

        # 1. Order tracking intent (direct to ShoppingAgent / tracking context)
        if any(w in msg_lower for w in ["track", "where is my order", "order status", "delivery status", "arrival", "eta"]):
            return {
                "target_agent": "ShoppingAgent",
                "intent": "track_order",
                "confidence": 0.98,
                "reasoning": "Explicit live tracking intent detected.",
            }

        # 2. Store selection / locking intent
        if any(w in msg_lower for w in ["select ", "lock to ", "switch to ", "order from ", "shop at "]):
            return {
                "target_agent": "ShoppingAgent",
                "intent": "store_lock",
                "confidence": 0.95,
                "reasoning": "Explicit merchant storefront selection detected.",
            }

        # 3. Checkout and payment intent
        if any(w in msg_lower for w in [
            "checkout", "pay now", "payment link", "proceed to pay", "make payment",
            "to a payment", "to payment", "do payment", "do a payment", "pay for me",
            "make a payment", "pay the bill", "pay bill", "open payment", "open razorpay"
        ]) or (msg_lower in ["pay", "payment"] or msg_lower.startswith("pay ") or msg_lower.endswith(" payment")):
            return {
                "target_agent": "ShoppingAgent",
                "intent": "checkout",
                "confidence": 0.96,
                "reasoning": "Direct checkout and payment trigger.",
            }

        # 4. Explicit exploration / city-wide discovery intent
        if any(w in msg_lower for w in [
            "explore all", "across city", "all stores", "other restaurants", "any store", "find anywhere",
            "some restro", "some restaurant", "another restaurant", "another store", "from other",
            "different restaurant", "different store", "somewhere else", "from somewhere", "other restro",
            "order both", "both orders", "dual", "from that shop", "from another", "and a pizza", "and pizza"
        ]):
            return {
                "target_agent": "DiscoveryAgent",
                "intent": "city_discovery",
                "confidence": 0.99,
                "reasoning": "Explicit cross-merchant exploration intent.",
            }

        # 5. Default based on current merchant lock
        if current_merchant is not None:
            return {
                "target_agent": "ShoppingAgent",
                "intent": "store_shopping",
                "confidence": 0.92,
                "reasoning": f"Customer session is locked to '{current_merchant.name}'.",
            }
        else:
            return {
                "target_agent": "DiscoveryAgent",
                "intent": "catalog_discovery",
                "confidence": 0.90,
                "reasoning": "No active merchant locked. Routing to city-wide discovery.",
            }

    async def route_customer_message(
        self,
        db: AsyncSession,
        merchant: Merchant | None,
        conversation: Conversation,
        user_message: str,
    ) -> ChatResponse:
        """Route customer chat messages based on conversation state."""
        from app.services.prompt_sanitizer import prompt_sanitizer

        sanitized_input = prompt_sanitizer.sanitize_customer_input(user_message)
        effective_message = sanitized_input["sanitized_text"]

        merchant = await self._resolve_merchant(db, merchant, conversation)
        routing_decision = self.classify_routing_intent(effective_message, current_merchant=merchant, cart=conversation.cart)
        logger.info("Routing decision: %s (confidence: %.2f) — %s", routing_decision["target_agent"], routing_decision["confidence"], routing_decision["reasoning"])

        target_agent = routing_decision.get("target_agent", "DiscoveryAgent")
        if merchant is None or target_agent == "DiscoveryAgent":
            logger.info("Routing request to DiscoveryAgent (City-Wide Mode)")
            resp = await self.discovery_agent.process_message(
                db=db,
                conversation=conversation,
                user_message=effective_message,
            )
        else:
            logger.info("Routing request to ShoppingAgent for merchant '%s'", merchant.name)
            resp = await self.shopping_agent.process_message(
                db=db,
                merchant=merchant,
                conversation=conversation,
                user_message=effective_message,
            )

        if resp and resp.message:
            resp.message = prompt_sanitizer.sanitize_agent_output(resp.message)["sanitized_text"]

        return resp

    async def route_customer_message_streaming(
        self,
        db: AsyncSession,
        merchant: Merchant | None,
        conversation: Conversation,
        user_message: str,
    ):
        """Route customer chat messages yielding real-time streaming ReAct reasoning events and latency traces."""
        from app.services.prompt_sanitizer import prompt_sanitizer
        from app.services.trace_service import TraceContext

        trace = TraceContext()
        r_span = trace.start_span("Intent Routing", category="router")

        # 1. Anti-Injection Security Filter
        sanitized_res = prompt_sanitizer.sanitize_customer_input(user_message)
        effective_message = sanitized_res["sanitized_text"]

        if not sanitized_res["is_safe"]:
            yield {
                "type": "security_check",
                "agent": "SecurityGuard",
                "content": f"🛡️ Sanitized prompt injection attempt: {', '.join(sanitized_res['flags'])}",
                "flags": sanitized_res["flags"],
            }

        merchant = await self._resolve_merchant(db, merchant, conversation)
        routing_info = self.classify_routing_intent(effective_message, current_merchant=merchant, cart=conversation.cart)
        r_span.finish({
            "target": routing_info["target_agent"],
            "confidence": routing_info["confidence"],
            "intent": routing_info["intent"],
        })

        # 2. Agent Routing & Execution Stream
        target_agent = routing_info.get("target_agent", "DiscoveryAgent")
        stream_gen = (
            self.discovery_agent.process_message_streaming(
                db=db,
                conversation=conversation,
                user_message=effective_message,
            )
            if (merchant is None or target_agent == "DiscoveryAgent")
            else self.shopping_agent.process_message_streaming(
                db=db,
                merchant=merchant,
                conversation=conversation,
                user_message=effective_message,
            )
        )

        async for event in stream_gen:
            if event.get("type") == "answer" and "content" in event:
                event["content"] = prompt_sanitizer.sanitize_agent_output(event["content"])["sanitized_text"]
            yield event

        # 3. Emit Structured Latency Trace Telemetry
        yield {
            "type": "trace",
            "agent": "ObservabilityTracer",
            "content": f"⚡ End-to-end turn completed in {trace.get_total_latency_ms():.1f}ms",
            "trace_data": trace.to_dict(),
            "telemetry_pills": trace.to_telemetry_pills(),
        }

    async def route_merchant_message(
        self,
        db: AsyncSession,
        merchant: Merchant,
        conversation: Conversation,
        user_message: str,
    ) -> dict[str, Any]:
        """Route merchant operational console queries."""
        from app.services.prompt_sanitizer import prompt_sanitizer

        sanitized_input = prompt_sanitizer.sanitize_customer_input(user_message)
        effective_message = sanitized_input["sanitized_text"]

        logger.info("Routing request to MerchantAgent for merchant '%s'", merchant.name)
        res = await self.merchant_agent.process_message(
            db=db,
            merchant=merchant,
            conversation=conversation,
            user_message=effective_message,
        )
        if isinstance(res, dict) and "message" in res and res["message"]:
            res["message"] = prompt_sanitizer.sanitize_agent_output(res["message"])["sanitized_text"]
        return res


agent_router = AgentRouter()
