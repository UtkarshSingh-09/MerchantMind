"""Agent Router — Multi-Agent Orchestrator for MerchantMind.
Routes incoming conversation requests to:
- DiscoveryAgent: When customer is exploring without a pre-selected store
- ShoppingAgent: When customer is locked into a specific merchant storefront
- MerchantAgent: When store manager is executing operations, stock management, or sales queries
"""

import logging
from typing import Any
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

    async def route_customer_message(
        self,
        db: AsyncSession,
        merchant: Merchant | None,
        conversation: Conversation,
        user_message: str,
    ) -> ChatResponse:
        """Route customer chat messages based on conversation state."""
        if merchant is None:
            logger.info("Routing request to DiscoveryAgent (City-Wide Mode)")
            return await self.discovery_agent.process_message(
                db=db,
                conversation=conversation,
                user_message=user_message,
            )
        else:
            logger.info("Routing request to ShoppingAgent for merchant '%s'", merchant.name)
            return await self.shopping_agent.process_message(
                db=db,
                merchant=merchant,
                conversation=conversation,
                user_message=user_message,
            )

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

        r_span.finish({"target": "DiscoveryAgent" if merchant is None else f"ShoppingAgent ({merchant.name})"})

        # 2. Agent Routing & Execution Stream
        if merchant is None:
            logger.info("Routing streaming request to DiscoveryAgent (City-Wide Mode)")
            async for event in self.discovery_agent.process_message_streaming(
                db=db,
                conversation=conversation,
                user_message=effective_message,
            ):
                yield event
        else:
            logger.info("Routing streaming request to ShoppingAgent for merchant '%s'", merchant.name)
            async for event in self.shopping_agent.process_message_streaming(
                db=db,
                merchant=merchant,
                conversation=conversation,
                user_message=effective_message,
            ):
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
        logger.info("Routing request to MerchantAgent for merchant '%s'", merchant.name)
        return await self.merchant_agent.process_message(
            db=db,
            merchant=merchant,
            conversation=conversation,
            user_message=user_message,
        )


agent_router = AgentRouter()
