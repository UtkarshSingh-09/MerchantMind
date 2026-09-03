"""Shopping Agent — Autonomous Single-Store Catalog Shopping, Smart Upselling & Razorpay Payments.
Manages customer carts, enforces budget guardrails with active alternatives, and completes Razorpay checkouts.
Supports real-time ReAct streaming of agent thinking, tool executions, and observations.
"""

import re
import json
import logging
import uuid
from typing import Any, AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession

STOPWORDS = {
    "hey", "hi", "hello", "please", "order", "me", "one", "two", "three", "four", "1", "2", "3", "4", "5",
    "i", "want", "to", "buy", "get", "need", "some", "a", "an", "the", "under",
    "below", "budget", "in", "for", "max", "rs", "rupees", "inr", "around", "approx",
    "can", "you", "show", "give", "and", "or", "with", "from", "of", "something", "like", "find"
}


def extract_search_keywords(text: str) -> str:
    cleaned = re.sub(r"[^\w\s]", " ", text.lower())
    words = [w for w in cleaned.split() if w not in STOPWORDS and not w.isdigit()]
    return " ".join(words).strip()

from app.models.merchant import Merchant
from app.models.conversation import Conversation
from app.services.groq_client import groq_client
from app.services.catalog_search import (
    search_products,
    get_product_by_id,
    get_merchant_catalog_summary,
)
from app.services.upsell_engine import get_upsell_suggestions
from app.services.conversation_service import (
    add_message_to_conversation,
    update_conversation_cart,
    add_agent_reasoning,
)
from app.services.budget_extractor import extract_structured_budget
from app.services.audit_service import log_audit_event, AuditEventType
from app.services.memory_service import build_optimized_context, build_customer_profile_memory
from app.services.entity_resolver import entity_resolver
from app.services.inventory_sync_service import inventory_sync_service
from app.services import order_service
from app.schemas.chat import ProductRecommendation, CartItem, ChatResponse

logger = logging.getLogger(__name__)

SHOPPING_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_catalog",
            "description": "Search for products in the merchant's catalog by keyword, category, or price range.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search keyword (e.g. chocolate cake, croissant, dress)"},
                    "category": {"type": "string", "description": "Product category"},
                    "min_price": {"type": "number", "description": "Minimum price filter"},
                    "max_price": {"type": "number", "description": "Maximum price filter"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_upsell_suggestions",
            "description": "Find smart complementary add-ons and pairings for items currently in cart.",
            "parameters": {
                "type": "object",
                "properties": {
                    "budget_remaining": {"type": "number", "description": "Remaining budget margin"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "add_to_cart",
            "description": "Add an item to customer's shopping cart. Will check budget guardrails automatically.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {"type": "string", "description": "UUID of product to add"},
                    "product_name": {"type": "string", "description": "Product name if UUID is unknown"},
                    "quantity": {"type": "integer", "description": "Quantity to add (default: 1)"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "remove_from_cart",
            "description": "Remove an item from customer's shopping cart.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {"type": "string", "description": "UUID of product to remove"},
                    "product_name": {"type": "string", "description": "Name of product to remove"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "view_cart",
            "description": "View current items in the cart and total cost.",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "clear_cart",
            "description": "Clear all items from customer's shopping cart.",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "checkout_and_pay",
            "description": "Create a Razorpay order and generate a secure test payment link.",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_name": {"type": "string", "description": "Customer name if known"},
                    "customer_phone": {"type": "string", "description": "Customer phone number if known"},
                    "fulfillment_mode": {
                        "type": "string",
                        "enum": ["delivery", "pickup"],
                        "description": "Fulfillment preference: 'delivery' for doorstep or 'pickup' for store counter",
                    },
                },
            },
        },
    },
]


def _build_shopping_prompt(
    merchant: Merchant,
    catalog_summary: list[dict[str, Any]],
    current_cart: dict[str, Any],
    handoff_context: dict[str, Any] | None = None,
    customer_memory: str = "",
) -> str:
    cart_items = current_cart.get("items", [])
    cart_total = current_cart.get("total", 0.0)
    budget_cfg = current_cart.get("budget") or {}
    budget_cap = budget_cfg.get("budget_amount")
    is_hard = budget_cfg.get("is_hard_limit", False)

    cart_summary_str = "Empty"
    if cart_items:
        cart_summary_str = ", ".join(
            [f"{item.get('quantity', 1)}x {item.get('name')} (₹{item.get('price')})" for item in cart_items]
        ) + f" | Total: ₹{cart_total:.0f}"

    budget_status_str = "None set"
    if budget_cap:
        budget_status_str = f"₹{budget_cap:.0f} ({'STRICT MAXIMUM' if is_hard else 'Flexible Target'}) | Remaining: ₹{max(0, budget_cap - cart_total):.0f}"

    catalog_lines = []
    for item in catalog_summary:
        catalog_lines.append(
            f"- [{item['id']}] {item['name']} | ₹{item['price']} | Category: {item['category']} | {item['description']}"
        )
    catalog_text = "\n".join(catalog_lines)

    handoff_text = ""
    if handoff_context and (handoff_context.get("intent") or handoff_context.get("search_query")):
        handoff_text = f"""
🔗 MULTI-AGENT HANDOFF CONTEXT (From {handoff_context.get('source_agent', 'DiscoveryAgent')}):
- Customer Original Goal: {handoff_context.get('intent', 'N/A')}
- Search Query: {handoff_context.get('search_query', 'N/A')}
- User Discovered Items: {json.dumps(handoff_context.get('preferred_items', []))}
Seamlessly fulfill the customer's goal without asking them to repeat themselves!
"""

    memory_section = f"\n\n{customer_memory}\n" if customer_memory else ""

    return f"""You are ShoppingAgent in MerchantMind — the AI Shopping Concierge for '{merchant.name}'.
About the store: {merchant.description or 'Artisan & Specialty Store'}.
Store Location: {merchant.store_address or 'Bangalore, India'}
Currency: INR (₹).
{memory_section}
{handoff_text}
CATALOG OVERVIEW:
{catalog_text}

CUSTOMER CART:
{cart_summary_str}
BUDGET GUARDRAIL:
{budget_status_str}

RESPONSIBILITIES:
1. **Catalog Search & Recommendations**: Describe items vividly with exact prices in ₹XXX.
2. **Handle Out of Stock Gracefully**: If an item is out of stock, politely introduce the closest in-stock alternatives.
3. **Smart Upselling**: When items are added, call `get_upsell_suggestions` for natural pairings (e.g. candles for birthday cake, beverages for pastries).
4. **Hard Budget Guardrails**: NEVER exceed a customer's strict budget limit. If `add_to_cart` returns a budget guardrail block, politely explain the budget limit and suggest the returned within-budget alternatives.
5. **Checkout**: When customer wants to buy/pay, call `checkout_and_pay` to generate Razorpay link.
6. **Tone**: Warm, enthusiastic, concise, and helpful.
"""


class ShoppingAgent:
    """Agent executing single-store catalog shopping, upselling, and Razorpay payments."""

    async def _execute_tool(
        self,
        db: AsyncSession,
        merchant: Merchant,
        conversation: Conversation,
        fn_name: str,
        fn_args: dict[str, Any],
        cart: dict[str, Any],
        recommendations: list[ProductRecommendation],
    ) -> tuple[dict[str, Any], str, str | None, dict[str, Any]]:
        """Execute a shopping tool and return (tool_result, action_type, payment_link, updated_cart)."""
        action_type = "chat"
        payment_link = None
        tool_result: dict[str, Any] = {}

        if fn_name == "search_catalog":
            action_type = "recommend"
            query = fn_args.get("query")
            category = fn_args.get("category")
            min_p = fn_args.get("min_price")
            max_p = fn_args.get("max_price")

            found_products = await search_products(
                db, merchant.id,
                query=query, category=category,
                min_price=min_p, max_price=max_p,
                limit=5,
            )
            exact_found = len(found_products) > 0
            if not found_products and query:
                found_products = await search_products(db, merchant.id, category=category, limit=4)
                if not found_products:
                    found_products = await search_products(db, merchant.id, limit=4)

            tool_result = {
                "exact_match": exact_found,
                "found_count": len(found_products),
                "user_query": query,
                "instruction": (
                    f"Found {len(found_products)} products for '{query}' in {merchant.name}."
                    if exact_found
                    else f"No direct match for '{query}' in {merchant.name}. Introduce these {len(found_products)} store alternatives warmly."
                ),
                "products": [
                    {
                        "id": str(p.id),
                        "name": p.name,
                        "price": p.price,
                        "category": p.category,
                        "description": p.description,
                        "image_url": p.image_url,
                    }
                    for p in found_products
                ],
            }
            for p in found_products:
                if not any(str(r.product_id) == str(p.id) for r in recommendations):
                    recommendations.append(
                        ProductRecommendation(
                            product_id=p.id,
                            name=p.name,
                            price=p.price,
                            description=p.description,
                            image_url=p.image_url,
                            category=p.category,
                            reasoning=f"Available at {merchant.name} for ₹{p.price:.0f}",
                        )
                    )

        elif fn_name == "get_upsell_suggestions":
            action_type = "upsell"
            budget_rem = fn_args.get("budget_remaining")
            cart_items = cart.get("items", [])

            upsell_items = await get_upsell_suggestions(
                db=db,
                merchant_id=merchant.id,
                cart_items=cart_items,
                budget_remaining=budget_rem,
                limit=3,
            )
            tool_result = {
                "suggested_count": len(upsell_items),
                "suggestions": upsell_items,
            }
            for u in upsell_items:
                pid = uuid.UUID(u["product_id"])
                if not any(str(r.product_id) == str(pid) for r in recommendations):
                    recommendations.append(
                        ProductRecommendation(
                            product_id=pid,
                            name=u["name"],
                            price=u["price"],
                            category=u.get("category"),
                            image_url=u.get("image_url"),
                            reasoning=u.get("reasoning", "Complementary store favorite"),
                        )
                    )
            add_agent_reasoning(
                conversation,
                action="upsell_recommendation",
                reasoning=f"Suggested {len(upsell_items)} complementary items for cart: {[u['name'] for u in upsell_items]}",
            )

        elif fn_name == "add_to_cart":
            action_type = "cart_update"
            pid = fn_args.get("product_id")
            pname = fn_args.get("product_name")
            qty = int(fn_args.get("quantity", 1))

            product = None
            if pid:
                try:
                    product = await get_product_by_id(db, merchant.id, uuid.UUID(pid))
                except Exception:
                    product = None
            if not product and pname:
                searched = await search_products(db, merchant.id, query=pname, limit=1)
                if searched:
                    product = searched[0]

            if product:
                items = list(cart.get("items", []))
                existing_item = next((i for i in items if str(i.get("product_id")) == str(product.id)), None)

                budget_cfg = cart.get("budget") or {}
                budget_cap = budget_cfg.get("budget_amount")
                is_hard_limit = budget_cfg.get("is_hard_limit", False)

                current_total = float(cart.get("total", 0.0))
                additional_cost = product.price * qty
                projected_total = current_total + additional_cost

                # Strict Budget Guardrail Check
                if is_hard_limit and budget_cap and (projected_total > budget_cap):
                    remaining_margin = max(0.0, budget_cap - current_total)
                    # Query in-budget alternatives for the merchant
                    in_budget_alts = await search_products(
                        db, merchant.id, max_price=remaining_margin if remaining_margin > 0 else None, limit=3
                    )
                    alt_list = [
                        {"name": a.name, "price": a.price, "category": a.category, "id": str(a.id)}
                        for a in in_budget_alts
                    ]

                    tool_result = {
                        "success": False,
                        "budget_blocked": True,
                        "current_total": current_total,
                        "projected_total": projected_total,
                        "budget_limit": budget_cap,
                        "remaining_budget": remaining_margin,
                        "attempted_product": product.name,
                        "attempted_price": product.price,
                        "suggested_in_budget_alternatives": alt_list,
                        "message": (
                            f"Budget Guardrail Active: Adding {qty}x {product.name} (₹{additional_cost:.0f}) brings total to ₹{projected_total:.0f}, "
                            f"exceeding your strict budget of ₹{budget_cap:.0f} (Remaining: ₹{remaining_margin:.0f})."
                        ),
                    }
                    add_agent_reasoning(
                        conversation,
                        action="budget_guardrail_blocked",
                        reasoning=f"Blocked {qty}x {product.name} (₹{additional_cost:.0f}): Projected ₹{projected_total:.0f} > hard budget ₹{budget_cap:.0f}. Found {len(alt_list)} in-budget alternatives.",
                    )
                    await log_audit_event(
                        db=db,
                        event_type=AuditEventType.BUDGET_VIOLATION,
                        merchant_id=merchant.id,
                        conversation_id=conversation.id,
                        action="add_to_cart_budget_blocked",
                        reasoning=f"Item addition blocked: ₹{projected_total:.0f} > budget limit ₹{budget_cap:.0f}",
                        input_data={"product": product.name, "additional": additional_cost, "budget": budget_cap},
                        output_data={"blocked": True, "alternatives": alt_list},
                    )
                else:
                    if existing_item:
                        existing_item["quantity"] = existing_item.get("quantity", 1) + qty
                    else:
                        items.append({
                            "product_id": str(product.id),
                            "name": product.name,
                            "price": product.price,
                            "quantity": qty,
                            "image_url": product.image_url,
                            "category": product.category,
                        })
                    cart["items"] = items
                    update_conversation_cart(conversation, cart)
                    cart = conversation.cart

                    tool_result = {
                        "success": True,
                        "added_product": product.name,
                        "quantity": qty,
                        "cart_total": cart["total"],
                        "cart_items": cart["items"],
                        "budget_remaining": (budget_cap - cart["total"]) if budget_cap else None,
                    }
                    add_agent_reasoning(
                        conversation,
                        action="add_to_cart",
                        reasoning=f"Added {qty}x {product.name} (₹{product.price:.0f}) to cart. Total: ₹{cart['total']:.0f}" + (f" (Remaining budget: ₹{budget_cap - cart['total']:.0f})" if budget_cap else ""),
                    )
                    await log_audit_event(
                        db=db,
                        event_type=AuditEventType.AGENT_DECISION,
                        merchant_id=merchant.id,
                        conversation_id=conversation.id,
                        action="add_to_cart",
                        reasoning=f"Added {qty}x {product.name} to cart. Total: ₹{cart['total']:.0f}",
                        input_data=fn_args,
                        output_data={"cart_total": cart["total"]},
                    )
            else:
                tool_result = {"success": False, "error": f"Product '{pname or pid}' not found."}

        elif fn_name == "remove_from_cart":
            action_type = "cart_update"
            pid = fn_args.get("product_id")
            pname = fn_args.get("product_name")
            items = list(cart.get("items", []))
            initial_len = len(items)

            if pid:
                items = [i for i in items if str(i.get("product_id")) != str(pid)]
            elif pname:
                items = [i for i in items if pname.lower() not in i.get("name", "").lower()]

            cart["items"] = items
            update_conversation_cart(conversation, cart)
            cart = conversation.cart
            tool_result = {"success": len(items) < initial_len, "cart_total": cart["total"]}

        elif fn_name == "view_cart":
            tool_result = cart

        elif fn_name == "clear_cart":
            action_type = "cart_update"
            cart["items"] = []
            update_conversation_cart(conversation, cart)
            cart = conversation.cart
            tool_result = {"success": True, "message": "Cart cleared"}

        elif fn_name == "checkout_and_pay":
            action_type = "checkout"
            cname = fn_args.get("customer_name")
            cphone = fn_args.get("customer_phone")
            f_mode = fn_args.get("fulfillment_mode", "delivery")

            try:
                order = await order_service.create_order(
                    db=db,
                    merchant_id=merchant.id,
                    conversation_id=conversation.id,
                    customer_name=cname,
                    customer_phone=cphone,
                    fulfillment_mode=f_mode,
                )
                payment_link = order.payment_link
                tool_result = {
                    "success": True,
                    "order_id": str(order.id),
                    "order_total": order.total,
                    "payment_link": payment_link,
                    "fulfillment_mode": order.fulfillment_mode,
                    "status": order.status,
                }
                add_agent_reasoning(
                    conversation,
                    action="checkout_and_pay",
                    reasoning=f"Generated Razorpay Order #{str(order.id)[:8]} for ₹{order.total:.0f}. Payment link created.",
                )
            except ValueError as budget_err:
                logger.warning("Checkout blocked by budget guardrail: %s", budget_err)
                tool_result = {"success": False, "guardrail_error": str(budget_err)}
            except Exception as e:
                logger.error("Checkout execution error: %s", e)
                tool_result = {"success": False, "error": str(e)}

        return tool_result, action_type, payment_link, cart

    async def process_message(
        self,
        db: AsyncSession,
        merchant: Merchant,
        conversation: Conversation,
        user_message: str,
    ) -> ChatResponse:
        """Process customer message synchronously (returns complete ChatResponse)."""
        cart = conversation.cart or {"items": [], "total": 0.0}

        # 1. Add user message
        add_message_to_conversation(conversation, role="user", content=user_message)

        # 2. Extract structured budget
        try:
            extracted_budget = await extract_structured_budget(conversation.messages or [])
            if extracted_budget.get("budget_amount") is not None:
                cart["budget"] = extracted_budget
                add_agent_reasoning(
                    conversation,
                    action="budget_extraction",
                    reasoning=f"Detected budget: ₹{extracted_budget['budget_amount']} ({'Strict Maximum' if extracted_budget['is_hard_limit'] else 'Flexible/Approximate'}). '{extracted_budget.get('raw_phrase')}'",
                )
                await log_audit_event(
                    db=db,
                    event_type=AuditEventType.BUDGET_CHECK,
                    merchant_id=merchant.id,
                    conversation_id=conversation.id,
                    action="budget_extracted",
                    reasoning=f"Extracted budget ₹{extracted_budget['budget_amount']} (hard={extracted_budget['is_hard_limit']})",
                    input_data={"phrase": extracted_budget.get("raw_phrase")},
                    output_data=extracted_budget,
                )
        except Exception as b_err:
            logger.warning("Budget extraction error in shopping agent: %s", b_err)

        # 3. Deterministic Entity Resolution & Multi-Item Edit Acceleration
        all_store_prods = [
            {"id": str(p.id), "name": p.name, "price": p.price}
            for p in (await search_products(db, merchant.id, limit=40))
        ]
        resolved_edit = await entity_resolver.parse_and_resolve_cart_edits(
            user_message=user_message,
            cart_items=cart.get("items", []),
            available_products=all_store_prods,
        )

        if resolved_edit.get("is_cart_edit"):
            if resolved_edit.get("clarifications"):
                clarification_text = " ".join(resolved_edit["clarifications"])
                add_message_to_conversation(conversation, role="assistant", content=clarification_text)
                return ChatResponse(
                    message=clarification_text,
                    cart=cart,
                    action_type="chat",
                    merchant_name=merchant.name,
                )

            if resolved_edit.get("actions"):
                summary_ops = []
                for op in resolved_edit["actions"]:
                    if op["action"] == "remove":
                        cart_items = [i for i in cart.get("items", []) if str(i.get("product_id")) != str(op["product_id"])]
                        cart["items"] = cart_items
                        cart["total"] = sum(float(i.get("unit_price", 0)) * int(i.get("quantity", 1)) for i in cart_items)
                        summary_ops.append(f"• Removed **{op['name']}** from cart")
                    elif op["action"] == "add":
                        existing = next((i for i in cart.get("items", []) if str(i.get("product_id")) == str(op["product_id"])), None)
                        if existing:
                            existing["quantity"] = int(existing.get("quantity", 1)) + int(op["quantity"])
                        else:
                            cart.setdefault("items", []).append({
                                "product_id": str(op["product_id"]),
                                "name": op["name"],
                                "unit_price": op["unit_price"],
                                "quantity": op["quantity"],
                            })
                        cart["total"] = sum(float(i.get("unit_price", 0)) * int(i.get("quantity", 1)) for i in cart["items"])
                        summary_ops.append(f"• Added **{op['quantity']}x {op['name']}** (₹{op['unit_price'] * op['quantity']:.0f})")

                update_conversation_cart(conversation, cart)
                add_agent_reasoning(
                    conversation,
                    action="entity_resolution",
                    reasoning=f"Deterministically executed compound cart update: {', '.join(summary_ops)}",
                )
                final_msg = f"I've updated your order at **{merchant.name}**:\n" + "\n".join(summary_ops) + f"\n\n🛒 **Cart Total: ₹{cart.get('total', 0):.0f}**\nWould you like to add anything else or proceed to checkout?"
                add_message_to_conversation(conversation, role="assistant", content=final_msg)
                return ChatResponse(
                    message=final_msg,
                    cart=cart,
                    action_type="cart_update",
                    merchant_name=merchant.name,
                )

        catalog_summary = await get_merchant_catalog_summary(db, merchant.id, limit=30)
        customer_mem = await build_customer_profile_memory(conversation.customer_id, db)
        system_prompt = _build_shopping_prompt(
            merchant=merchant,
            catalog_summary=catalog_summary,
            current_cart=cart,
            handoff_context=conversation.handoff_context,
            customer_memory=customer_mem,
        )

        # Memory optimization: sliding window + summarization
        optimized_history = await build_optimized_context(conversation, max_recent=6)

        llm_messages: list[dict[str, Any]] = [
            {"role": "system", "content": system_prompt},
            *optimized_history,
        ]

        recommendations: list[ProductRecommendation] = []
        action_type = "chat"
        payment_link: str | None = None
        final_text = ""

        try:
            for _ in range(2):
                response = await groq_client.chat_completion(
                    messages=llm_messages,
                    tools=SHOPPING_TOOLS,
                    tool_choice="auto",
                    temperature=0.2,
                    max_tokens=350,
                )
                response_msg = response.choices[0].message
                tool_calls = getattr(response_msg, "tool_calls", None)

                if not tool_calls:
                    final_text = response_msg.content or f"How may I assist you at {merchant.name}?"
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

                    t_res, act, plink, updated_cart = await self._execute_tool(
                        db=db,
                        merchant=merchant,
                        conversation=conversation,
                        fn_name=fn_name,
                        fn_args=fn_args,
                        cart=cart,
                        recommendations=recommendations,
                    )
                    cart = updated_cart
                    if act != "chat":
                        action_type = act
                    if plink:
                        payment_link = plink

                    llm_messages.append({
                        "role": "tool",
                        "tool_call_id": tool.id,
                        "name": fn_name,
                        "content": json.dumps(t_res),
                    })

            if not final_text:
                final_text = f"I've updated your order for {merchant.name}. Ready to checkout or explore more items?"

        except Exception as exc:
            logger.error("ShoppingAgent error: %s", exc, exc_info=True)
            final_text = "I've processed your store request. How else can I assist with your order?"

        cart_items_list = [
            CartItem(
                product_id=uuid.UUID(i["product_id"]) if isinstance(i["product_id"], str) else i["product_id"],
                name=i["name"],
                price=float(i["price"]),
                quantity=int(i.get("quantity", 1)),
            )
            for i in cart.get("items", [])
        ]

        add_message_to_conversation(
            conversation,
            role="assistant",
            content=final_text,
            metadata={
                "recommendations": [r.model_dump(mode="json") for r in recommendations],
                "action": action_type,
                "payment_link": payment_link,
            },
        )

        return ChatResponse(
            conversation_id=conversation.id,
            merchant_id=merchant.id,
            merchant_name=merchant.name,
            message=final_text,
            recommendations=recommendations if recommendations else None,
            cart=cart_items_list if cart_items_list else None,
            cart_total=float(cart.get("total", 0.0)),
            action=action_type,
            payment_link=payment_link,
            agent_reasoning=conversation.agent_reasoning if conversation.agent_reasoning else None,
        )

    async def process_message_streaming(
        self,
        db: AsyncSession,
        merchant: Merchant,
        conversation: Conversation,
        user_message: str,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Process message in real-time streaming mode, yielding ReAct reasoning events and final response."""
        cart = conversation.cart or {"items": [], "total": 0.0}

        # Event: Started thinking
        yield {
            "type": "thinking",
            "agent": "ShoppingAgent",
            "content": f"Analyzing request for '{merchant.name}': \"{user_message}\"",
        }

        # 1. Add user message
        add_message_to_conversation(conversation, role="user", content=user_message)

        # 2. Extract structured budget
        try:
            extracted_budget = await extract_structured_budget(conversation.messages or [])
            if extracted_budget.get("budget_amount") is not None:
                cart["budget"] = extracted_budget
                yield {
                    "type": "budget_check",
                    "agent": "ShoppingAgent",
                    "content": f"Identified budget constraint: ₹{extracted_budget['budget_amount']} ({'Strict limit' if extracted_budget['is_hard_limit'] else 'Flexible target'})",
                    "data": extracted_budget,
                }
                add_agent_reasoning(
                    conversation,
                    action="budget_extraction",
                    reasoning=f"Detected budget: ₹{extracted_budget['budget_amount']} ({'Strict Maximum' if extracted_budget['is_hard_limit'] else 'Flexible/Approximate'}). '{extracted_budget.get('raw_phrase')}'",
                )
                await log_audit_event(
                    db=db,
                    event_type=AuditEventType.BUDGET_CHECK,
                    merchant_id=merchant.id,
                    conversation_id=conversation.id,
                    action="budget_extracted",
                    reasoning=f"Extracted budget ₹{extracted_budget['budget_amount']} (hard={extracted_budget['is_hard_limit']})",
                    input_data={"phrase": extracted_budget.get("raw_phrase")},
                    output_data=extracted_budget,
                )
        except Exception as b_err:
            logger.warning("Budget extraction error in shopping agent: %s", b_err)

        # If handoff context exists, emit notification
        if conversation.handoff_context and conversation.handoff_context.get("intent"):
            yield {
                "type": "handoff_context_applied",
                "agent": "ShoppingAgent",
                "content": f"Inherited intent from Discovery Agent: \"{conversation.handoff_context.get('intent')}\"",
                "data": conversation.handoff_context,
            }

        # 3. Deterministic Entity Resolution & Multi-Item Edit Acceleration
        all_store_prods = [
            {"id": str(p.id), "name": p.name, "price": p.price}
            for p in (await search_products(db, merchant.id, limit=40))
        ]
        resolved_edit = await entity_resolver.parse_and_resolve_cart_edits(
            user_message=user_message,
            cart_items=cart.get("items", []),
            available_products=all_store_prods,
        )

        if resolved_edit.get("is_cart_edit"):
            if resolved_edit.get("clarifications"):
                clarification_text = " ".join(resolved_edit["clarifications"])
                yield {
                    "type": "thinking",
                    "agent": "ShoppingAgent",
                    "content": f"Ambiguity detected in cart instruction. Formulating clarification request...",
                }
                add_message_to_conversation(conversation, role="assistant", content=clarification_text)
                yield {
                    "type": "answer",
                    "agent": "ShoppingAgent",
                    "content": clarification_text,
                    "data": {
                        "cart": cart,
                        "action_type": "chat",
                        "merchant_name": merchant.name,
                        "recommendations": [],
                    },
                }
                return

            if resolved_edit.get("actions"):
                yield {
                    "type": "tool_call",
                    "agent": "ShoppingAgent",
                    "content": f"Fast-resolving {len(resolved_edit['actions'])} cart modifications (95%+ match confidence)...",
                }
                summary_ops = []
                for op in resolved_edit["actions"]:
                    if op["action"] == "remove":
                        cart_items = [i for i in cart.get("items", []) if str(i.get("product_id")) != str(op["product_id"])]
                        cart["items"] = cart_items
                        cart["total"] = sum(float(i.get("unit_price", 0)) * int(i.get("quantity", 1)) for i in cart_items)
                        summary_ops.append(f"• Removed **{op['name']}** from cart")
                    elif op["action"] == "add":
                        existing = next((i for i in cart.get("items", []) if str(i.get("product_id")) == str(op["product_id"])), None)
                        if existing:
                            existing["quantity"] = int(existing.get("quantity", 1)) + int(op["quantity"])
                        else:
                            cart.setdefault("items", []).append({
                                "product_id": str(op["product_id"]),
                                "name": op["name"],
                                "unit_price": op["unit_price"],
                                "quantity": op["quantity"],
                            })
                        cart["total"] = sum(float(i.get("unit_price", 0)) * int(i.get("quantity", 1)) for i in cart["items"])
                        summary_ops.append(f"• Added **{op['quantity']}x {op['name']}** (₹{op['unit_price'] * op['quantity']:.0f})")

                update_conversation_cart(conversation, cart)
                yield {
                    "type": "tool_result",
                    "agent": "ShoppingAgent",
                    "content": f"Updated cart total: ₹{cart.get('total', 0):.0f} ({len(cart.get('items', []))} items)",
                }
                add_agent_reasoning(
                    conversation,
                    action="entity_resolution",
                    reasoning=f"Deterministically executed compound cart update: {', '.join(summary_ops)}",
                )
                final_msg = f"I've updated your order at **{merchant.name}**:\n" + "\n".join(summary_ops) + f"\n\n🛒 **Cart Total: ₹{cart.get('total', 0):.0f}**\nWould you like to add anything else or proceed to checkout?"
                add_message_to_conversation(conversation, role="assistant", content=final_msg)
                yield {
                    "type": "answer",
                    "agent": "ShoppingAgent",
                    "content": final_msg,
                    "data": {
                        "cart": cart,
                        "action_type": "cart_update",
                        "merchant_name": merchant.name,
                        "recommendations": [],
                    },
                }
                return

        catalog_summary = await get_merchant_catalog_summary(db, merchant.id, limit=30)
        customer_mem = await build_customer_profile_memory(conversation.customer_id, db)
        system_prompt = _build_shopping_prompt(
            merchant=merchant,
            catalog_summary=catalog_summary,
            current_cart=cart,
            handoff_context=conversation.handoff_context,
            customer_memory=customer_mem,
        )

        optimized_history = await build_optimized_context(conversation, max_recent=6)

        llm_messages: list[dict[str, Any]] = [
            {"role": "system", "content": system_prompt},
            *optimized_history,
        ]

        recommendations: list[ProductRecommendation] = []
        action_type = "chat"
        payment_link: str | None = None
        final_text = ""

        # 4. Speculative In-Store Catalog Fast-Path (<5ms local search)
        spec_kw = extract_search_keywords(user_message)
        budget_amt = cart.get("budget", {}).get("budget_amount")
        if len(spec_kw) >= 3:
            spec_prods = await search_products(db, merchant_id=merchant.id, query=spec_kw, max_price=budget_amt, limit=6)
            if spec_prods:
                action_type = "recommend"
                for p in spec_prods[:4]:
                    recommendations.append(
                        ProductRecommendation(
                            product_id=p.id,
                            name=p.name,
                            price=float(p.price),
                            description=p.description or "",
                            image_url=p.image_url,
                            category=p.category,
                            reasoning=f"Available at {merchant.name} — ₹{p.price:.0f}",
                        )
                    )
                yield {
                    "type": "tool_call",
                    "agent": "ShoppingAgent",
                    "tool": "search_catalog",
                    "tool_display": "Search Catalog",
                    "args": {"query": spec_kw, "max_price": budget_amt},
                    "content": f"Searching {merchant.name} catalog for `{spec_kw}`...",
                }
                yield {
                    "type": "tool_result",
                    "agent": "ShoppingAgent",
                    "tool": "search_catalog",
                    "summary": f"Found {len(spec_prods)} matching items in {merchant.name}",
                    "data": {
                        "exact_match": True,
                        "found_count": len(spec_prods),
                        "products": [{"name": p.name, "price": p.price} for p in spec_prods],
                    },
                }
                call_id = f"call_spec_{uuid.uuid4().hex[:6]}"
                llm_messages.append({
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [{
                        "id": call_id,
                        "type": "function",
                        "function": {
                            "name": "search_catalog",
                            "arguments": json.dumps({"query": spec_kw, "max_price": budget_amt}),
                        },
                    }],
                })
                llm_messages.append({
                    "role": "tool",
                    "tool_call_id": call_id,
                    "name": "search_catalog",
                    "content": json.dumps({
                        "found_count": len(spec_prods),
                        "products": [{"name": p.name, "price": p.price} for p in spec_prods],
                        "instruction": f"Found {len(spec_prods)} matching items for '{spec_kw}'. Present these options in an appetizing, beautifully formatted Markdown table with columns (#, Dish/Item, Price in ₹). Mention budget guardrails and provide clear numbered options for the user to add to cart or checkout.",
                    }),
                })

        try:
            for cycle_idx in range(2):
                yield {
                    "type": "thinking",
                    "agent": "ShoppingAgent",
                    "content": f"Synthesizing catalog state and cart constraints (Cycle {cycle_idx + 1})...",
                }

                response = await groq_client.chat_completion(
                    messages=llm_messages,
                    tools=SHOPPING_TOOLS if not spec_prods else None,
                    tool_choice="auto" if not spec_prods else "none",
                    temperature=0.25,
                    max_tokens=500,
                )
                response_msg = response.choices[0].message
                tool_calls = getattr(response_msg, "tool_calls", None)

                if not tool_calls:
                    final_text = response_msg.content or f"How may I assist you at {merchant.name}?"
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

                    # Emit tool_call event
                    tool_display_name = fn_name.replace("_", " ").title()
                    yield {
                        "type": "tool_call",
                        "agent": "ShoppingAgent",
                        "tool": fn_name,
                        "tool_display": tool_display_name,
                        "args": fn_args,
                        "content": f"Calling `{fn_name}` with {json.dumps(fn_args)}",
                    }

                    t_res, act, plink, updated_cart = await self._execute_tool(
                        db=db,
                        merchant=merchant,
                        conversation=conversation,
                        fn_name=fn_name,
                        fn_args=fn_args,
                        cart=cart,
                        recommendations=recommendations,
                    )
                    cart = updated_cart
                    if act != "chat":
                        action_type = act
                    if plink:
                        payment_link = plink

                    # Summarize tool observation for ReAct stream
                    summary = ""
                    if fn_name == "search_catalog":
                        summary = f"Found {t_res.get('found_count', 0)} matching products in {merchant.name}"
                    elif fn_name == "add_to_cart":
                        if t_res.get("budget_blocked"):
                            summary = f"⚠️ Budget guardrail blocked addition: total would reach ₹{t_res.get('projected_total')} > limit ₹{t_res.get('budget_limit')}"
                        else:
                            summary = f"✅ Added to cart. New Total: ₹{t_res.get('cart_total', 0)}"
                    elif fn_name == "get_upsell_suggestions":
                        summary = f"Found {t_res.get('suggested_count', 0)} complementary upsell pairings"
                    elif fn_name == "checkout_and_pay":
                        summary = f"💳 Generated Razorpay payment link for ₹{t_res.get('order_total', 0)}"
                    else:
                        summary = f"Completed {fn_name}"

                    yield {
                        "type": "tool_result",
                        "agent": "ShoppingAgent",
                        "tool": fn_name,
                        "summary": summary,
                        "data": t_res,
                    }

                    llm_messages.append({
                        "role": "tool",
                        "tool_call_id": tool.id,
                        "name": fn_name,
                        "content": json.dumps(t_res),
                    })

            if not final_text:
                final_text = f"I've updated your order for {merchant.name}. Ready to checkout or explore more items?"

        except Exception as exc:
            logger.error("ShoppingAgent streaming error: %s", exc, exc_info=True)
            final_text = "I've processed your store request. How else can I assist with your order?"

        cart_items_list = [
            CartItem(
                product_id=uuid.UUID(i["product_id"]) if isinstance(i["product_id"], str) else i["product_id"],
                name=i["name"],
                price=float(i["price"]),
                quantity=int(i.get("quantity", 1)),
            )
            for i in cart.get("items", [])
        ]

        add_message_to_conversation(
            conversation,
            role="assistant",
            content=final_text,
            metadata={
                "recommendations": [r.model_dump(mode="json") for r in recommendations],
                "action": action_type,
                "payment_link": payment_link,
            },
        )

        chat_resp = ChatResponse(
            conversation_id=conversation.id,
            merchant_id=merchant.id,
            merchant_name=merchant.name,
            message=final_text,
            recommendations=recommendations if recommendations else None,
            cart=cart_items_list if cart_items_list else None,
            cart_total=float(cart.get("total", 0.0)),
            action=action_type,
            payment_link=payment_link,
            agent_reasoning=conversation.agent_reasoning if conversation.agent_reasoning else None,
        )

        # Final event: Answer with full ChatResponse payload
        yield {
            "type": "answer",
            "agent": "ShoppingAgent",
            "content": final_text,
            "chat_response": chat_resp.model_dump(mode="json"),
        }


shopping_agent = ShoppingAgent()
