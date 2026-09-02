"""Merchant Operations & Growth Agent.
Autonomous AI agent for store managers to manage inventory, analyze real-time sales,
prevent stockouts, and recover abandoned carts through conversational commands.
"""

import json
import logging
import uuid
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.merchant import Merchant
from app.models.conversation import Conversation
from app.services.groq_client import groq_client
from app.services.audit_service import log_audit_event, AuditEventType
from app.services import merchant_service

logger = logging.getLogger(__name__)

MERCHANT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_sales_summary",
            "description": "Get real-time sales analytics and order counts for a time period (today, yesterday, this_week, this_month, last_7_days).",
            "parameters": {
                "type": "object",
                "properties": {
                    "period": {
                        "type": "string",
                        "enum": ["today", "yesterday", "this_week", "this_month", "last_7_days", "last_30_days"],
                        "description": "Time frame to aggregate sales for",
                    },
                },
                "required": ["period"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_stock",
            "description": "Update product stock status (in stock / sold out) and/or price. Use when merchant says 'sold out of red velvet', 'chocolate cake is 699 now', or 'mark tomatoes back in stock'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_name": {
                        "type": "string",
                        "description": "Name or keyword of the product to update",
                    },
                    "in_stock": {
                        "type": "boolean",
                        "description": "True if item is available/in stock, False if sold out",
                    },
                    "new_price": {
                        "type": "number",
                        "description": "Optional updated price in INR",
                    },
                },
                "required": ["product_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "suggest_reorder",
            "description": "Analyze recent order velocity, stock levels, and flag items that are out of stock or trending fast.",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_abandoned_carts",
            "description": "Scan recent shopping sessions for unpurchased carts that can be re-engaged.",
            "parameters": {
                "type": "object",
                "properties": {
                    "min_value": {
                        "type": "number",
                        "description": "Optional minimum cart value to filter",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "draft_recovery_message",
            "description": "Generate an engaging, personalized WhatsApp/SMS recovery draft for an abandoned customer cart.",
            "parameters": {
                "type": "object",
                "properties": {
                    "conversation_id": {
                        "type": "string",
                        "description": "UUID of the abandoned conversation",
                    },
                    "tone": {
                        "type": "string",
                        "enum": ["friendly", "urgent", "discount_offer"],
                        "description": "Tone for the recovery message",
                    },
                },
                "required": ["conversation_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generate_promotion",
            "description": "Create a high-converting Razorpay promotional coupon code, discount campaign, and marketing copy.",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "Optional category to target (e.g. Breads, Pastries, Cakes, Biryani)",
                    },
                    "discount_percentage": {
                        "type": "integer",
                        "description": "Discount percentage (default: 15)",
                    },
                    "reason": {
                        "type": "string",
                        "description": "Business objective (e.g. clear weekend stock, new customer acquisition)",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "customer_sentiment_summary",
            "description": "Analyze recent customer shopping conversations to detect trending product demand, common questions, and sentiment.",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
]


def _build_merchant_system_prompt(merchant: Merchant, stats: dict[str, Any]) -> str:
    return f"""You are MerchantMind Operations & Growth Agent — the dedicated AI co-pilot for '{merchant.name}'.
Store Description: {merchant.description or 'Specialty Retail & Food Store'}.

📊 LIVE STORE TELEMETRY:
- Total Catalog Items: {stats.get('product_count', 0)} ({stats.get('in_stock_count', 0)} Active, {stats.get('out_of_stock', 0)} Sold Out)
- Orders Today: {stats.get('orders_today', 0)} ({stats.get('paid_orders_today', 0)} Paid via Razorpay)
- Gross Revenue Today: ₹{stats.get('revenue_today', 0.0):.2f}

🎯 YOUR OPERATIONAL CAPABILITIES:
1. **Sales & Revenue Intelligence**: Call `get_sales_summary` when the merchant asks about daily/weekly/monthly revenue, top-selling items, or average order value. Always format results in clear markdown tables!
2. **Instant Inventory Updates**: Call `update_stock` when the merchant mentions stock changes (e.g., "we're out of red velvet cake", "mark mango yogurt back in stock", "change sourdough price to ₹150").
3. **Restocking & Demand Alerts**: Call `suggest_reorder` to identify high-velocity items at risk of running out.
4. **Cart Abandonment Recovery**: Call `get_abandoned_carts` and `draft_recovery_message` to help the merchant follow up on high-intent lost sales.

FORMATTING & TONE:
- Be professional, sharp, and data-driven like a chief operating officer.
- Use markdown tables for multi-row data.
- Format all currency cleanly as ₹XXX.
- Confirm any database modifications clearly with bold highlights.
"""


class MerchantAgent:
    """Agent executing store operations, inventory modifications, and revenue intelligence."""

    async def process_message(
        self,
        db: AsyncSession,
        merchant: Merchant,
        conversation: Conversation,
        user_message: str,
    ) -> dict[str, Any]:
        """Execute merchant agent interaction loop."""
        stats = await merchant_service.get_store_stats(db, merchant.id)
        system_prompt = _build_merchant_system_prompt(merchant, stats)

        llm_messages: list[dict[str, Any]] = [
            {"role": "system", "content": system_prompt}
        ]

        # Add recent conversation history (last 8 messages)
        raw_msgs = (conversation.messages or [])[-8:]
        for m in raw_msgs:
            role = m.get("role", "user")
            content = m.get("content", "")
            if role in ["user", "assistant"] and content:
                llm_messages.append({"role": role, "content": content})

        llm_messages.append({"role": "user", "content": user_message})

        final_text = ""
        action_data: dict[str, Any] = {}

        try:
            # 3-cycle tool execution and explanation loop
            for _ in range(3):
                response = await groq_client.chat_completion(
                    messages=llm_messages,
                    tools=MERCHANT_TOOLS,
                    tool_choice="auto",
                    temperature=0.2,
                )
                response_msg = response.choices[0].message
                tool_calls = getattr(response_msg, "tool_calls", None)

                if not tool_calls:
                    final_text = response_msg.content or "How may I assist with your store operations?"
                    break

                assistant_dict = {
                    "role": "assistant",
                    "content": response_msg.content or None,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments,
                            },
                        }
                        for tc in tool_calls
                    ],
                }
                llm_messages.append(assistant_dict)

                for tool in tool_calls:
                    fn_name = tool.function.name
                    try:
                        fn_args = json.loads(tool.function.arguments or "{}")
                    except Exception:
                        fn_args = {}

                    tool_result: dict[str, Any] = {}

                    if fn_name == "get_sales_summary":
                        period = fn_args.get("period", "today")
                        tool_result = await merchant_service.get_sales_for_period(db, merchant.id, period)
                        action_data["sales_summary"] = tool_result
                        await log_audit_event(
                            db=db,
                            event_type=AuditEventType.AGENT_DECISION,
                            merchant_id=merchant.id,
                            conversation_id=conversation.id,
                            action="sales_summary_query",
                            reasoning=f"Generated sales summary for period: {period}",
                            input_data=fn_args,
                            output_data=tool_result,
                        )

                    elif fn_name == "update_stock":
                        pname = fn_args.get("product_name", "")
                        in_stock = fn_args.get("in_stock")
                        new_p = fn_args.get("new_price")
                        tool_result = await merchant_service.update_product_stock_and_price(
                            db, merchant.id, pname, in_stock=in_stock, new_price=new_p
                        )
                        action_data["stock_update"] = tool_result
                        await log_audit_event(
                            db=db,
                            event_type=AuditEventType.AGENT_DECISION,
                            merchant_id=merchant.id,
                            conversation_id=conversation.id,
                            action="product_inventory_update",
                            reasoning=f"Updated inventory for '{pname}': {tool_result.get('changes')}",
                            input_data=fn_args,
                            output_data=tool_result,
                        )

                    elif fn_name == "suggest_reorder":
                        tool_result = await merchant_service.get_trending_and_reorder_alerts(db, merchant.id)
                        action_data["reorder_alerts"] = tool_result
                        await log_audit_event(
                            db=db,
                            event_type=AuditEventType.AGENT_DECISION,
                            merchant_id=merchant.id,
                            conversation_id=conversation.id,
                            action="reorder_alerts_scanned",
                            reasoning=f"Scanned velocity: {len(tool_result.get('out_of_stock_items', []))} out of stock, {len(tool_result.get('trending_items', []))} trending.",
                            input_data={},
                            output_data=tool_result,
                        )

                    elif fn_name == "get_abandoned_carts":
                        min_v = float(fn_args.get("min_value", 0.0))
                        abandoned = await merchant_service.get_abandoned_conversations(db, merchant.id, min_v)
                        tool_result = {
                            "abandoned_count": len(abandoned),
                            "total_recoverable_value": sum(a["cart_total"] for a in abandoned),
                            "abandoned_carts": abandoned,
                        }
                        action_data["abandoned_carts"] = tool_result
                        await log_audit_event(
                            db=db,
                            event_type=AuditEventType.AGENT_DECISION,
                            merchant_id=merchant.id,
                            conversation_id=conversation.id,
                            action="abandoned_carts_scanned",
                            reasoning=f"Found {len(abandoned)} abandoned carts totaling ₹{tool_result['total_recoverable_value']:.0f}",
                            input_data=fn_args,
                            output_data=tool_result,
                        )

                    elif fn_name == "draft_recovery_message":
                        conv_id_str = fn_args.get("conversation_id")
                        tone = fn_args.get("tone", "friendly")
                        try:
                            conv_uuid = uuid.UUID(conv_id_str)
                            tool_result = await merchant_service.generate_recovery_draft(
                                db, merchant.id, conv_uuid, tone=tone
                            )
                        except Exception as e:
                            tool_result = {"success": False, "error": str(e)}
                        action_data["recovery_draft"] = tool_result
                        await log_audit_event(
                            db=db,
                            event_type=AuditEventType.AGENT_DECISION,
                            merchant_id=merchant.id,
                            conversation_id=conversation.id,
                            action="draft_recovery_message",
                            reasoning=f"Drafted {tone} recovery message for conversation {conv_id_str}",
                            input_data=fn_args,
                            output_data=tool_result,
                        )

                    elif fn_name == "generate_promotion":
                        cat = fn_args.get("category")
                        disc = int(fn_args.get("discount_percentage", 15))
                        reason = fn_args.get("reason", "Clear stock and drive revenue")
                        tool_result = await merchant_service.generate_promotion_campaign(
                            db=db,
                            merchant_id=merchant.id,
                            category=cat,
                            discount_pct=disc,
                            reason=reason,
                        )
                        action_data["promotion"] = tool_result
                        await log_audit_event(
                            db=db,
                            event_type=AuditEventType.AGENT_DECISION,
                            merchant_id=merchant.id,
                            conversation_id=conversation.id,
                            action="generate_promotion",
                            reasoning=f"Created promotion coupon '{tool_result.get('coupon_code')}' for {disc}% OFF",
                            input_data=fn_args,
                            output_data=tool_result,
                        )

                    elif fn_name == "customer_sentiment_summary":
                        tool_result = await merchant_service.analyze_customer_sentiment(
                            db=db,
                            merchant_id=merchant.id,
                        )
                        action_data["sentiment_analysis"] = tool_result
                        await log_audit_event(
                            db=db,
                            event_type=AuditEventType.AGENT_DECISION,
                            merchant_id=merchant.id,
                            conversation_id=conversation.id,
                            action="customer_sentiment_analysis",
                            reasoning=f"Analyzed customer sentiment across {tool_result.get('conversation_count', 0)} sessions",
                            input_data={},
                            output_data=tool_result,
                        )

                    llm_messages.append({
                        "role": "tool",
                        "tool_call_id": tool.id,
                        "name": fn_name,
                        "content": json.dumps(tool_result),
                    })

            if not final_text:
                final_text = "I have executed your store operation. What else would you like to review?"

        except Exception as exc:
            logger.error("MerchantAgent error: %s", exc, exc_info=True)
            final_text = f"I've processed your store request. Let me know if you'd like to check sales or update stock."

        return {
            "message": final_text,
            "action_data": action_data,
            "merchant_id": str(merchant.id),
            "merchant_name": merchant.name,
        }


merchant_agent = MerchantAgent()
