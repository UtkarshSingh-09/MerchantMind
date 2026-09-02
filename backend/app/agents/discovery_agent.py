"""Discovery Agent — Autonomous Cross-Merchant City-Wide Product Discovery.
Scans multi-merchant inventories, generates comparison tables, enforces budget guardrails,
and executes seamless handoff to ShoppingAgent upon merchant selection.
Supports real-time ReAct streaming of agent thinking, tool executions, and observations.
"""

import json
import logging
import uuid
from typing import Any, AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation
from app.services.groq_client import groq_client
from app.services.catalog_search import (
    search_all_merchants_catalog,
    get_all_merchants_summary,
    get_product_by_id_any_merchant,
)
from app.services.conversation_service import (
    add_message_to_conversation,
    add_agent_reasoning,
    lock_conversation_to_merchant,
    update_conversation_cart,
    set_handoff_context,
)
from app.services.budget_extractor import extract_structured_budget
from app.services.audit_service import log_audit_event, AuditEventType
from app.services.memory_service import build_optimized_context
from app.schemas.chat import ProductRecommendation, CartItem, ChatResponse

logger = logging.getLogger(__name__)

DISCOVERY_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_all_stores",
            "description": "Search products across ALL city merchants by keyword, category, or budget. Use when customer has no specific store preference and wants to discover options.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Product search keywords (e.g. chocolate cake, biryani, sourdough, filter coffee)",
                    },
                    "category": {
                        "type": "string",
                        "description": "Category filter (e.g. Cakes, Pastries, Biryani, South Indian, North Indian, Chinese, Beverages)",
                    },
                    "max_price": {
                        "type": "number",
                        "description": "Maximum budget in INR — only return items within this budget",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_available_stores",
            "description": "List all registered merchants in the city with their specialties, category counts, and price ranges.",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "select_store",
            "description": "Lock the customer into a specific merchant store after they choose one. Prepares handoff context.",
            "parameters": {
                "type": "object",
                "properties": {
                    "merchant_id": {
                        "type": "string",
                        "description": "UUID of the merchant to lock into",
                    },
                    "merchant_name": {
                        "type": "string",
                        "description": "Display name of the merchant",
                    },
                },
                "required": ["merchant_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "add_to_cart",
            "description": "Add a discovered product to cart and lock into that product's merchant store with full handoff context.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {
                        "type": "string",
                        "description": "UUID of the product to add",
                    },
                    "product_name": {
                        "type": "string",
                        "description": "Product name if UUID is unknown",
                    },
                    "quantity": {
                        "type": "integer",
                        "description": "Quantity to add (default: 1)",
                    },
                },
            },
        },
    },
]


def _build_discovery_prompt(city_merchants: list[dict[str, Any]], current_cart: dict[str, Any]) -> str:
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

    stores_text = "\n".join([
        f"- {m['name']} (ID: {m['id']}) | Categories: {', '.join([c.get('name', '') if isinstance(c, dict) else str(c) for c in m.get('categories', [])])} | Products: {m.get('product_count', 0)} | Price Range: {m.get('price_range', '')}"
        for m in city_merchants[:20]
    ])

    return f"""You are DiscoveryAgent in MerchantMind — the Autonomous City-Wide Shopping Concierge across Bangalore.
Your mission is to help customers explore, discover, and compare products across ALL 48 registered Bangalore food stores and bakeries.
Currency: INR (₹).

CITY STORES DIRECTORY (Sample):
{stores_text}

CUSTOMER CART:
{cart_summary_str}
BUDGET GUARDRAIL:
{budget_status_str}

RESPONSIBILITIES:
1. **Explore & Search Across Stores**: Call `search_all_stores` when the customer asks for any food item, category, or generic craving.
2. **Present Clear Comparisons**: Compare stores by price, specialty, and product quality. Always mention store names and prices in ₹XXX clearly.
3. **Hard Budget Guardrails**: When searching or recommending, prioritize items within the customer's budget limit.
4. **Smart Handoff**: When a customer picks a product or store, call `select_store` or `add_to_cart` to lock into that merchant and transition smoothly.
5. **Tone**: Warm, knowledgeable, comparative, and proactive.
"""


class DiscoveryAgent:
    """Agent executing cross-merchant catalog discovery and smart handoffs."""

    async def _execute_tool(
        self,
        db: AsyncSession,
        conversation: Conversation,
        fn_name: str,
        fn_args: dict[str, Any],
        cart: dict[str, Any],
        city_merchants: list[dict[str, Any]],
        recommendations: list[ProductRecommendation],
        last_search_query: str,
    ) -> tuple[dict[str, Any], str, uuid.UUID | None, str | None, dict[str, Any], str]:
        """Execute discovery tool and return (tool_result, action_type, resolved_id, resolved_name, updated_cart, query)."""
        action_type = "chat"
        resolved_merchant_id = None
        resolved_merchant_name = None
        tool_result: dict[str, Any] = {}

        if fn_name == "search_all_stores":
            action_type = "recommend"
            query = fn_args.get("query")
            category = fn_args.get("category")
            max_p = fn_args.get("max_price")
            last_search_query = query or category or ""

            found = await search_all_merchants_catalog(
                db, query=query, category=category, max_price=max_p, limit=10
            )
            exact_found = len(found) > 0
            if not found and query:
                found = await search_all_merchants_catalog(db, category=category, limit=6)
                if not found:
                    found = await search_all_merchants_catalog(db, limit=6)

            tool_result = {
                "exact_match": exact_found,
                "found_count": len(found),
                "user_query": query,
                "products": found,
                "instruction": (
                    f"Found {len(found)} products for '{query}' across city merchants."
                    if exact_found
                    else f"No direct match for '{query}'. Introduce these {len(found)} closest store alternatives warmly."
                ),
            }
            for p in found:
                pid = uuid.UUID(p["id"])
                if not any(str(r.product_id) == str(pid) for r in recommendations):
                    recommendations.append(
                        ProductRecommendation(
                            product_id=pid,
                            name=p["name"],
                            price=p["price"],
                            description=p.get("description"),
                            image_url=p.get("image_url"),
                            category=p.get("category"),
                            reasoning=f"From {p['merchant_name']} — ₹{p['price']}",
                        )
                    )
            add_agent_reasoning(
                conversation,
                action="search_all_stores",
                reasoning=f"Cross-merchant search: query='{query}', category='{category}', max_price={max_p}. Found {len(found)} items.",
            )

        elif fn_name == "list_available_stores":
            tool_result = {
                "store_count": len(city_merchants),
                "stores": city_merchants,
            }
            add_agent_reasoning(
                conversation,
                action="list_available_stores",
                reasoning=f"Listed {len(city_merchants)} available merchants in city.",
            )

        elif fn_name == "select_store":
            merchant_id_str = fn_args.get("merchant_id")
            store_name = fn_args.get("merchant_name", "")
            try:
                selected_id = uuid.UUID(merchant_id_str)
                handoff_data = {
                    "intent": f"Shop at {store_name}",
                    "search_query": last_search_query,
                    "budget": cart.get("budget"),
                    "preferred_items": [r.model_dump(mode="json") for r in recommendations[:4]],
                    "source_agent": "DiscoveryAgent",
                    "selected_store_name": store_name,
                }
                conversation = await lock_conversation_to_merchant(
                    db, conversation, selected_id, handoff_data=handoff_data
                )
                resolved_merchant_id = selected_id
                resolved_merchant_name = store_name
                tool_result = {
                    "success": True,
                    "locked_to": store_name,
                    "handoff_context": handoff_data,
                    "message": f"Successfully locked to {store_name}. Handing off to store ShoppingAgent!",
                }
                add_agent_reasoning(
                    conversation,
                    action="select_store_handoff",
                    reasoning=f"Handoff executed: Locked conversation to store '{store_name}' ({selected_id}). Context transferred.",
                )
                await log_audit_event(
                    db=db,
                    event_type=AuditEventType.AGENT_DECISION,
                    merchant_id=selected_id,
                    conversation_id=conversation.id,
                    action="agent_handoff",
                    reasoning=f"DiscoveryAgent -> ShoppingAgent for '{store_name}'",
                    input_data=fn_args,
                    output_data={"handoff": handoff_data},
                )
            except Exception as e:
                tool_result = {"success": False, "error": str(e)}

        elif fn_name == "add_to_cart":
            action_type = "cart_update"
            pid = fn_args.get("product_id")
            pname = fn_args.get("product_name")
            qty = int(fn_args.get("quantity", 1))

            product = None
            if pid:
                try:
                    product = await get_product_by_id_any_merchant(db, uuid.UUID(pid))
                except Exception:
                    product = None
            elif pname:
                try:
                    all_found = await search_all_merchants_catalog(db, query=pname, limit=1)
                    if all_found:
                        found_pid = uuid.UUID(all_found[0]["id"])
                        product = await get_product_by_id_any_merchant(db, found_pid)
                except Exception:
                    product = None

            if product:
                handoff_data = {
                    "intent": f"Buy {product.name}",
                    "search_query": last_search_query or product.name,
                    "budget": cart.get("budget"),
                    "preferred_items": [{"product_id": str(product.id), "name": product.name, "price": product.price}],
                    "source_agent": "DiscoveryAgent",
                }
                conversation = await lock_conversation_to_merchant(
                    db, conversation, product.merchant_id, handoff_data=handoff_data
                )
                resolved_merchant_id = product.merchant_id

                items = list(cart.get("items", []))
                existing_item = next((i for i in items if str(i.get("product_id")) == str(product.id)), None)
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
                    "locked_to_merchant": str(product.merchant_id),
                }
                add_agent_reasoning(
                    conversation,
                    action="add_to_cart_discovery",
                    reasoning=f"Added {qty}x {product.name} (₹{product.price:.0f}) to cart and locked conversation to store {product.merchant_id}.",
                )
                await log_audit_event(
                    db=db,
                    event_type=AuditEventType.AGENT_DECISION,
                    merchant_id=product.merchant_id,
                    conversation_id=conversation.id,
                    action="add_to_cart_discovery",
                    reasoning=f"Added {qty}x {product.name} to cart. Total: ₹{cart['total']:.0f}",
                    input_data=fn_args,
                    output_data={"cart_total": cart["total"]},
                )
            else:
                tool_result = {"success": False, "error": f"Product '{pname or pid}' not found across stores."}

        return tool_result, action_type, resolved_merchant_id, resolved_merchant_name, cart, last_search_query

    async def process_message(
        self,
        db: AsyncSession,
        conversation: Conversation,
        user_message: str,
    ) -> ChatResponse:
        """Process customer message synchronously in Discovery Mode."""
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
        except Exception as b_err:
            logger.warning("Budget extraction error in discovery agent: %s", b_err)

        city_merchants = await get_all_merchants_summary(db)
        system_prompt = _build_discovery_prompt(city_merchants, cart)

        optimized_history = await build_optimized_context(conversation, max_recent=6)

        llm_messages: list[dict[str, Any]] = [
            {"role": "system", "content": system_prompt},
            *optimized_history,
        ]

        recommendations: list[ProductRecommendation] = []
        action_type = "chat"
        payment_link: str | None = None
        final_text = ""
        resolved_merchant_id: uuid.UUID | None = None
        resolved_merchant_name: str | None = None
        last_search_query = ""

        try:
            for _ in range(3):
                response = await groq_client.chat_completion(
                    messages=llm_messages,
                    tools=DISCOVERY_TOOLS,
                    tool_choice="auto",
                    temperature=0.3,
                )
                response_msg = response.choices[0].message
                tool_calls = getattr(response_msg, "tool_calls", None)

                if not tool_calls:
                    final_text = response_msg.content or "How may I assist your search across city stores?"
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

                    t_res, act, r_id, r_name, updated_cart, last_search_query = await self._execute_tool(
                        db=db,
                        conversation=conversation,
                        fn_name=fn_name,
                        fn_args=fn_args,
                        cart=cart,
                        city_merchants=city_merchants,
                        recommendations=recommendations,
                        last_search_query=last_search_query,
                    )
                    cart = updated_cart
                    if act != "chat":
                        action_type = act
                    if r_id:
                        resolved_merchant_id = r_id
                    if r_name:
                        resolved_merchant_name = r_name

                    llm_messages.append({
                        "role": "tool",
                        "tool_call_id": tool.id,
                        "name": fn_name,
                        "content": json.dumps(t_res),
                    })

            if not final_text:
                final_text = "I've discovered these options across Bangalore stores for you. Which store would you like to explore?"

        except Exception as exc:
            logger.error("DiscoveryAgent error: %s", exc, exc_info=True)
            final_text = "I ran a city-wide search across Bangalore stores. How else can I assist?"

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
                "resolved_merchant_id": str(resolved_merchant_id) if resolved_merchant_id else None,
            },
        )

        return ChatResponse(
            conversation_id=conversation.id,
            merchant_id=resolved_merchant_id,
            merchant_name=resolved_merchant_name,
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
        conversation: Conversation,
        user_message: str,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Process message in real-time streaming mode, yielding ReAct reasoning events and final response."""
        cart = conversation.cart or {"items": [], "total": 0.0}

        # Event: Initial Thought
        yield {
            "type": "thinking",
            "agent": "DiscoveryAgent",
            "content": f"Exploring city-wide options across 48 Bangalore stores: \"{user_message}\"",
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
                    "agent": "DiscoveryAgent",
                    "content": f"Customer budget filter applied: ₹{extracted_budget['budget_amount']} ({'Hard limit' if extracted_budget['is_hard_limit'] else 'Soft target'})",
                    "data": extracted_budget,
                }
                add_agent_reasoning(
                    conversation,
                    action="budget_extraction",
                    reasoning=f"Detected budget: ₹{extracted_budget['budget_amount']} ({'Strict Maximum' if extracted_budget['is_hard_limit'] else 'Flexible/Approximate'}). '{extracted_budget.get('raw_phrase')}'",
                )
        except Exception as b_err:
            logger.warning("Budget extraction error in discovery agent: %s", b_err)

        city_merchants = await get_all_merchants_summary(db)
        system_prompt = _build_discovery_prompt(city_merchants, cart)

        optimized_history = await build_optimized_context(conversation, max_recent=6)

        llm_messages: list[dict[str, Any]] = [
            {"role": "system", "content": system_prompt},
            *optimized_history,
        ]

        recommendations: list[ProductRecommendation] = []
        action_type = "chat"
        payment_link: str | None = None
        final_text = ""
        resolved_merchant_id: uuid.UUID | None = None
        resolved_merchant_name: str | None = None
        last_search_query = ""

        try:
            for cycle_idx in range(3):
                yield {
                    "type": "thinking",
                    "agent": "DiscoveryAgent",
                    "content": f"Scanning cross-merchant inventory and pricing (Cycle {cycle_idx + 1})...",
                }

                response = await groq_client.chat_completion(
                    messages=llm_messages,
                    tools=DISCOVERY_TOOLS,
                    tool_choice="auto",
                    temperature=0.3,
                )
                response_msg = response.choices[0].message
                tool_calls = getattr(response_msg, "tool_calls", None)

                if not tool_calls:
                    final_text = response_msg.content or "How may I assist your search across city stores?"
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

                    tool_display_name = fn_name.replace("_", " ").title()
                    yield {
                        "type": "tool_call",
                        "agent": "DiscoveryAgent",
                        "tool": fn_name,
                        "tool_display": tool_display_name,
                        "args": fn_args,
                        "content": f"Executing `{fn_name}` with {json.dumps(fn_args)}",
                    }

                    t_res, act, r_id, r_name, updated_cart, last_search_query = await self._execute_tool(
                        db=db,
                        conversation=conversation,
                        fn_name=fn_name,
                        fn_args=fn_args,
                        cart=cart,
                        city_merchants=city_merchants,
                        recommendations=recommendations,
                        last_search_query=last_search_query,
                    )
                    cart = updated_cart
                    if act != "chat":
                        action_type = act
                    if r_id:
                        resolved_merchant_id = r_id
                    if r_name:
                        resolved_merchant_name = r_name

                    # Summarize tool observation
                    summary = ""
                    if fn_name == "search_all_stores":
                        summary = f"Found {t_res.get('found_count', 0)} matching items across Bangalore merchants"
                    elif fn_name == "select_store":
                        summary = f"🔒 Locked to '{r_name}'. Context prepared for Shopping Agent handoff"
                        yield {
                            "type": "handoff",
                            "agent": "DiscoveryAgent",
                            "target_agent": "ShoppingAgent",
                            "store_name": r_name,
                            "content": f"Transferred customer intent and discovered items to {r_name} Shopping Agent.",
                        }
                    elif fn_name == "add_to_cart":
                        summary = f"Added {t_res.get('added_product')} to cart & locked to merchant."
                    elif fn_name == "list_available_stores":
                        summary = f"Retrieved {t_res.get('store_count', 0)} registered Bangalore stores."
                    else:
                        summary = f"Completed {fn_name}"

                    yield {
                        "type": "tool_result",
                        "agent": "DiscoveryAgent",
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
                final_text = "I've discovered these options across Bangalore stores for you. Which store would you like to explore?"

        except Exception as exc:
            logger.error("DiscoveryAgent streaming error: %s", exc, exc_info=True)
            final_text = "I ran a city-wide search across Bangalore stores. How else can I assist?"

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
                "resolved_merchant_id": str(resolved_merchant_id) if resolved_merchant_id else None,
            },
        )

        chat_resp = ChatResponse(
            conversation_id=conversation.id,
            merchant_id=resolved_merchant_id,
            merchant_name=resolved_merchant_name,
            message=final_text,
            recommendations=recommendations if recommendations else None,
            cart=cart_items_list if cart_items_list else None,
            cart_total=float(cart.get("total", 0.0)),
            action=action_type,
            payment_link=payment_link,
            agent_reasoning=conversation.agent_reasoning if conversation.agent_reasoning else None,
        )

        yield {
            "type": "answer",
            "agent": "DiscoveryAgent",
            "content": final_text,
            "chat_response": chat_resp.model_dump(mode="json"),
        }


discovery_agent = DiscoveryAgent()
