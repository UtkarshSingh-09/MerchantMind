"""Checkout & Growth Agent with Cross-Merchant Discovery Mode, smart upselling, Razorpay payments, and Audit Guardrails."""

import json
import logging
import uuid
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation
from app.models.merchant import Merchant
from app.services.groq_client import groq_client
from app.services.catalog_search import (
    search_products,
    get_product_by_id,
    get_product_by_id_any_merchant,
    get_merchant_catalog_summary,
    search_all_merchants_catalog,
    get_all_merchants_summary,
)
from app.services.upsell_engine import get_upsell_suggestions
from app.services.conversation_service import (
    add_message_to_conversation,
    update_conversation_cart,
    add_agent_reasoning,
    lock_conversation_to_merchant,
)
from app.services.audit_service import log_audit_event, AuditEventType
from app.services.budget_extractor import extract_structured_budget
from app.services import order_service
from app.schemas.chat import ProductRecommendation, CartItem, ChatResponse

logger = logging.getLogger(__name__)


# ─── Discovery Mode Tools (cross-merchant search) ──────────────────────────────
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
                        "description": "Product search keywords (e.g. chocolate cake, grocery, shirt, birthday gift)",
                    },
                    "category": {
                        "type": "string",
                        "description": "Category filter (e.g. Cakes, Pastries, Groceries, Clothing)",
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
            "description": "List all available stores/merchants in the city with their specialties, product counts, and price ranges.",
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
            "description": "Lock the conversation to a specific merchant/store. Call this AFTER the customer confirms which store's product they want to buy. Once locked, the cart and checkout will be for this store only.",
            "parameters": {
                "type": "object",
                "properties": {
                    "merchant_id": {
                        "type": "string",
                        "description": "UUID of the merchant/store to lock into",
                    },
                    "merchant_name": {
                        "type": "string",
                        "description": "Name of the selected store for confirmation",
                    },
                },
                "required": ["merchant_id"],
            },
        },
    },
]


# ─── Shopping Mode Tools (single-merchant cart/checkout) ────────────────────────
SHOPPING_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_catalog",
            "description": "Search products in the selected merchant's catalog by keyword, category, or price range.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Product search keywords (e.g. chocolate cake, croissant, candle)",
                    },
                    "category": {
                        "type": "string",
                        "description": "Category filter (e.g. Cakes, Pastries, Combos, Breads, Beverages, Party Supplies)",
                    },
                    "min_price": {
                        "type": "number",
                        "description": "Minimum price in INR",
                    },
                    "max_price": {
                        "type": "number",
                        "description": "Maximum price in INR (budget cap)",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "add_to_cart",
            "description": "Add an item to customer's shopping cart by product ID or name.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {
                        "type": "string",
                        "description": "UUID of the product to add",
                    },
                    "product_name": {
                        "type": "string",
                        "description": "Name of the product if ID not available",
                    },
                    "quantity": {
                        "type": "integer",
                        "description": "Quantity to add (default 1)",
                        "default": 1,
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_upsell_suggestions",
            "description": "Get smart complementary add-ons and combo recommendations based on items in customer's cart and remaining budget.",
            "parameters": {
                "type": "object",
                "properties": {
                    "budget_remaining": {
                        "type": "number",
                        "description": "Remaining budget amount in INR after current cart total, if customer mentioned a budget limit",
                    },
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
                    "product_id": {
                        "type": "string",
                        "description": "UUID of the product to remove",
                    },
                    "product_name": {
                        "type": "string",
                        "description": "Name of product to remove if ID is unknown",
                    },
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
            "description": "Create a Razorpay order from customer's cart and generate a secure payment link. Call when the customer wants to checkout, pay, or place the order.",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_name": {
                        "type": "string",
                        "description": "Customer name if known",
                    },
                    "customer_phone": {
                        "type": "string",
                        "description": "Customer phone number if known",
                    },
                },
            },
        },
    },
]


# ─── System Prompt Builders ─────────────────────────────────────────────────────

def _build_discovery_prompt(city_merchants: list[dict[str, Any]], current_cart: dict[str, Any]) -> str:
    """Build system prompt for Discovery Mode — no merchant selected yet."""
    merchants_text = ""
    for m in city_merchants:
        cats = ", ".join([f"{c['name']} ({c['count']})" for c in m.get("categories", [])])
        merchants_text += f"  • {m['name']} — {m['description'] or 'Specialty store'}\n"
        merchants_text += f"    Categories: {cats}\n"
        merchants_text += f"    Price range: {m['price_range']} | {m['product_count']} products\n\n"

    return f"""You are MerchantMind — an autonomous AI Shopping Agent that discovers the BEST store and products for customers across the entire city.

🏙️ AVAILABLE STORES IN THE CITY:
{merchants_text}

🧠 YOUR DISCOVERY RESPONSIBILITIES:
1. **Warm Welcome**: Greet the customer and ask: "Do you have a specific store in mind, or should I find the best options across all stores?"
2. **If customer has a specific store**: Call `list_available_stores` to show them available stores. Once they pick one, call `select_store` to lock in.
3. **If customer says NO or just tells you what they want**: Ask about their budget and preferences, then call `search_all_stores` with the right filters.
4. **Present Results as Comparison**: Show a clear comparison — Store Name | Product | Price | Why it's a good match.
5. **Guide to Selection**: After showing options, help the customer pick the best option. When they decide, call `select_store` to lock the merchant.
6. **After Store Lock**: Once a store is selected, switch to normal shopping mode — browse that store's catalog, add to cart, upsell, and checkout.

💰 BUDGET GUARDRAIL:
- If customer mentions a budget, ONLY search within that budget using max_price filter
- If Store A has nothing in budget but Store B does, recommend Store B!
- ALWAYS respect the budget — never suggest items above stated budget

🎯 CONVERSATION STYLE & LANGUAGE:
- ALWAYS RESPOND AND SPEAK EXCLUSIVELY IN 100% CLEAN, NATURAL, PROFESSIONAL ENGLISH.
- NEVER SPEAK IN HINDI, HINGLISH, URDU, OR CASUAL REGIONAL SLANG (NO "Bhai", "yaar", "toh", "yeh lo", "chahiye", "accha", etc.).
- Be warm, helpful, and proactive — like a knowledgeable local friend
- Use emojis sparingly for visual appeal
- Format prices cleanly as ₹XXX
- Keep responses concise but informative
"""


def _build_shopping_prompt(merchant: Merchant, catalog_summary: list[dict[str, Any]], current_cart: dict[str, Any]) -> str:
    """Build system prompt for Shopping Mode — merchant selected, browsing their catalog."""
    cart_items = current_cart.get("items", [])
    cart_total = current_cart.get("total", 0.0)

    cart_summary_str = "Empty"
    if cart_items:
        cart_summary_str = ", ".join(
            [f"{item.get('quantity', 1)}x {item.get('name')} (₹{item.get('price')})" for item in cart_items]
        ) + f" | Total: ₹{cart_total}"

    catalog_lines = []
    for item in catalog_summary:
        catalog_lines.append(
            f"- [{item['id']}] {item['name']} | ₹{item['price']} | Category: {item['category']} | {item['description']}"
        )
    catalog_text = "\n".join(catalog_lines)

    return f"""You are the friendly, intelligent AI Shopping & Growth Agent for '{merchant.name}'.
About the store: {merchant.description or 'Artisan bakery & specialty food store'}.
Store currency: INR (₹).

CURRENT CATALOG OVERVIEW:
{catalog_text}

CURRENT CUSTOMER CART:
{cart_summary_str}

YOUR RESPONSIBILITIES & PROACTIVE BEHAVIORS:
1. **Product Recommendation with Reasoning**: When customers ask for items (e.g. "I want a chocolate cake under ₹800" or "organic capsicum"), search the catalog or pick from catalog overview. ALWAYS explain WHAT you found and WHY you recommend each item.
2. **Handle Out of Stock Gracefully**: If the exact item requested is not in the store catalog, inform the customer politely: "We don't currently have [item] in stock at this store, but here are our closest fresh alternatives from our live catalog:" and introduce the alternatives!
3. **Proactive Smart Upselling & Cross-Selling**:
   - Whenever an item is added to cart, call `get_upsell_suggestions` to discover natural pairings!
   - Examples: If customer adds a Birthday Cake, suggest: "Would you like to complete the celebration with our Birthday Candles Set (₹50) or Balloon Combo (₹150)?"
   - If customer adds Pastries or Breads, suggest a freshly brewed Artisan Coffee or Cold Beverage!
4. **Respect Customer Budget (Hard Guardrail)**: NEVER recommend items exceeding customer's stated budget. If cart is ₹650 and budget is ₹800, remaining budget is ₹150 — only recommend add-ons ≤ ₹150!
5. **Cart Actions**: Call `add_to_cart` or `remove_from_cart` when customer asks to add/buy/remove items.
6. **Checkout & Payment**: When customer wants to checkout, proceed to payment, or buy the cart items, call `checkout_and_pay` tool. Present the generated payment link clearly.
7. **No Generic Placeholders**: NEVER output generic text like "I have updated your request. What else would you like to add?". Always speak conversationally, describe the items vividly, and provide helpful guidance!
8. **Strict English Requirement**: ALWAYS speak and respond exclusively in clean, natural, professional English. Never use Hindi or Hinglish slang.
"""


# ─── The Agent ───────────────────────────────────────────────────────────────────

class CheckoutAgent:
    """Agent orchestrating discovery, conversational commerce, smart upselling, Razorpay checkout, and audit logging."""

    async def process_message(
        self,
        db: AsyncSession,
        merchant: Merchant | None,
        conversation: Conversation,
        user_message: str,
    ) -> ChatResponse:
        """Process incoming customer message with Discovery or Shopping mode.

        If merchant is None → Discovery Mode (cross-merchant search)
        If merchant is set  → Shopping Mode (single-merchant catalog + checkout)
        """
        discovery_mode = (merchant is None)
        cart = conversation.cart or {"items": [], "total": 0.0}

        # 1. Add user message to conversation history
        add_message_to_conversation(conversation, role="user", content=user_message)

        # 2. Extract structured budget from recent conversation intent
        try:
            extracted_budget = await extract_structured_budget(conversation.messages or [])
            if extracted_budget.get("budget_amount") is not None:
                cart["budget"] = extracted_budget
                add_agent_reasoning(
                    conversation,
                    action="budget_extraction",
                    reasoning=f"Detected budget: ₹{extracted_budget['budget_amount']} ({'Strict Maximum' if extracted_budget['is_hard_limit'] else 'Flexible/Approximate'}). '{extracted_budget.get('raw_phrase')}'",
                )
                if merchant:
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
            logger.warning("Budget extraction error in agent: %s", b_err)

        # 3. Build system prompt and select tools based on mode
        if discovery_mode:
            city_merchants = await get_all_merchants_summary(db)
            system_prompt = _build_discovery_prompt(city_merchants, cart)
            tools = DISCOVERY_TOOLS + SHOPPING_TOOLS
        else:
            catalog_summary = await get_merchant_catalog_summary(db, merchant.id, limit=25)
            system_prompt = _build_shopping_prompt(merchant, catalog_summary, cart)
            tools = SHOPPING_TOOLS

        llm_messages: list[dict[str, Any]] = [
            {"role": "system", "content": system_prompt}
        ]

        # Add recent conversation history (last 10 messages)
        raw_msgs = (conversation.messages or [])[-10:]
        for m in raw_msgs:
            role = m.get("role", "user")
            content = m.get("content", "")
            if role in ["user", "assistant"] and content:
                llm_messages.append({"role": role, "content": content})

        recommendations: list[ProductRecommendation] = []
        action_type = "chat"
        payment_link: str | None = None
        final_text = ""
        resolved_merchant_id: uuid.UUID | None = merchant.id if merchant else None
        resolved_merchant_name: str | None = merchant.name if merchant else None

        try:
            # Multi-turn tool execution loop (max 3 cycles)
            for _ in range(3):
                response = await groq_client.chat_completion(
                    messages=llm_messages,
                    tools=tools,
                    tool_choice="auto",
                    temperature=0.3,
                )
                response_msg = response.choices[0].message
                tool_calls = getattr(response_msg, "tool_calls", None)

                if not tool_calls:
                    final_text = response_msg.content or "How may I assist you with your order?"
                    break

                # Append assistant message with tool calls as a clean JSON-serializable dict
                assistant_dict: dict[str, Any] = {
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

                # Process each tool call
                for tool in tool_calls:
                    fn_name = tool.function.name
                    try:
                        fn_args = json.loads(tool.function.arguments or "{}")
                    except Exception:
                        fn_args = {}

                    tool_result: dict[str, Any] = {}
                    logger.info("Executing tool %s with args %s", fn_name, fn_args)

                    # ── Discovery Mode Tools ─────────────────────────────

                    if fn_name == "search_all_stores":
                        action_type = "recommend"
                        query = fn_args.get("query")
                        category = fn_args.get("category")
                        max_p = fn_args.get("max_price")

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
                                f"Found {len(found)} products for '{query}'."
                                if exact_found
                                else f"No direct match for '{query}' across city stores. Tell the customer that '{query}' is not in stock, and introduce these {len(found)} fresh alternatives warmly."
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
                            reasoning=f"Cross-merchant search: query='{query}', category='{category}', max_price={max_p}. Found {len(found)} results (exact_match={exact_found}).",
                        )

                    elif fn_name == "list_available_stores":
                        city_merchants = await get_all_merchants_summary(db)
                        tool_result = {
                            "store_count": len(city_merchants),
                            "stores": city_merchants,
                        }
                        add_agent_reasoning(
                            conversation,
                            action="list_available_stores",
                            reasoning=f"Listed {len(city_merchants)} available merchants in the city.",
                        )

                    elif fn_name == "select_store":
                        merchant_id_str = fn_args.get("merchant_id")
                        store_name = fn_args.get("merchant_name", "")
                        try:
                            selected_id = uuid.UUID(merchant_id_str)
                            conversation = await lock_conversation_to_merchant(
                                db, conversation, selected_id
                            )
                            # Reload merchant for shopping mode
                            from sqlalchemy import select as sa_select
                            from app.models.merchant import Merchant as MerchantModel
                            stmt = sa_select(MerchantModel).where(MerchantModel.id == selected_id)
                            res = await db.execute(stmt)
                            merchant = res.scalar_one_or_none()
                            discovery_mode = False
                            resolved_merchant_id = selected_id
                            resolved_merchant_name = merchant.name if merchant else store_name

                            # Rebuild tools and prompt for shopping mode
                            catalog_summary = await get_merchant_catalog_summary(db, selected_id, limit=25)
                            tools = SHOPPING_TOOLS

                            tool_result = {
                                "success": True,
                                "locked_to": resolved_merchant_name,
                                "message": f"Great! You are now shopping at {resolved_merchant_name}. I can help you browse their catalog, add items to cart, and checkout.",
                            }
                            add_agent_reasoning(
                                conversation,
                                action="select_store",
                                reasoning=f"Locked conversation to merchant: {resolved_merchant_name} ({selected_id})",
                            )
                        except Exception as e:
                            tool_result = {"success": False, "error": f"Could not select store: {str(e)}"}

                    # ── Shopping Mode Tools ──────────────────────────────

                    elif fn_name == "search_catalog":
                        if not merchant:
                            tool_result = {"error": "No store selected yet. Use search_all_stores or select_store first."}
                        else:
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
                                    else f"No direct match for '{query}' in {merchant.name}. Tell customer that '{query}' is currently unavailable and introduce these {len(found_products)} alternative items warmly."
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
                                            reasoning=f"Available at {merchant.name} for ₹{p.price}",
                                        )
                                    )
                            await log_audit_event(
                                db=db,
                                event_type=AuditEventType.AGENT_DECISION,
                                merchant_id=merchant.id,
                                conversation_id=conversation.id,
                                action="search_catalog",
                                reasoning=f"Catalog search executed for '{query or category}'",
                                input_data=fn_args,
                                output_data={"found_count": len(found_products)},
                            )

                    elif fn_name == "get_upsell_suggestions":
                        if not merchant:
                            tool_result = {"error": "No store selected yet."}
                        else:
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
                                reasoning=f"Suggested {len(upsell_items)} complementary items: {[u['name'] for u in upsell_items]}",
                            )
                            await log_audit_event(
                                db=db,
                                event_type=AuditEventType.AGENT_DECISION,
                                merchant_id=merchant.id,
                                conversation_id=conversation.id,
                                action="get_upsell_suggestions",
                                reasoning=f"Upsell suggestions generated for {len(cart_items)} cart items",
                                input_data=fn_args,
                                output_data={"suggestions": [u["name"] for u in upsell_items]},
                            )

                    elif fn_name == "add_to_cart":
                        action_type = "cart_update"
                        pid = fn_args.get("product_id")
                        pname = fn_args.get("product_name")
                        qty = int(fn_args.get("quantity", 1))

                        product = None
                        if merchant:
                            # Shopping Mode: search within locked merchant
                            if pid:
                                try:
                                    product = await get_product_by_id(db, merchant.id, uuid.UUID(pid))
                                except Exception:
                                    product = None
                            if not product and pname:
                                searched = await search_products(db, merchant.id, query=pname, limit=1)
                                if searched:
                                    product = searched[0]
                        else:
                            # Discovery Mode: product might be from any merchant
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
                                # Auto-lock to this product's merchant
                                conversation = await lock_conversation_to_merchant(
                                    db, conversation, product.merchant_id
                                )
                                from sqlalchemy import select as sa_select
                                from app.models.merchant import Merchant as MerchantModel
                                stmt = sa_select(MerchantModel).where(MerchantModel.id == product.merchant_id)
                                res = await db.execute(stmt)
                                merchant = res.scalar_one_or_none()
                                discovery_mode = False
                                resolved_merchant_id = product.merchant_id
                                resolved_merchant_name = merchant.name if merchant else "Store"
                                tools = SHOPPING_TOOLS

                        if product:
                            items = list(cart.get("items", []))
                            existing_item = next((i for i in items if str(i.get("product_id")) == str(product.id)), None)

                            # Budget Guardrail Check
                            budget_cfg = cart.get("budget") or {}
                            budget_cap = budget_cfg.get("budget_amount")
                            is_hard_limit = budget_cfg.get("is_hard_limit", False)
                            
                            current_total = float(cart.get("total", 0.0))
                            additional_cost = product.price * qty
                            projected_total = current_total + additional_cost

                            if is_hard_limit and budget_cap and (projected_total > budget_cap):
                                tool_result = {
                                    "success": False,
                                    "budget_blocked": True,
                                    "current_total": current_total,
                                    "projected_total": projected_total,
                                    "budget_limit": budget_cap,
                                    "message": f"Hard budget guardrail triggered: Adding {qty}x {product.name} (₹{additional_cost:.0f}) brings total to ₹{projected_total:.0f}, which exceeds your stated limit of ₹{budget_cap:.0f}. Please adjust your quantity or choose a different item.",
                                }
                                add_agent_reasoning(
                                    conversation,
                                    action="budget_guardrail_blocked",
                                    reasoning=f"Blocked {qty}x {product.name} (₹{additional_cost:.0f}): Projected total ₹{projected_total:.0f} > hard budget ₹{budget_cap:.0f}",
                                )
                                if merchant:
                                    await log_audit_event(
                                        db=db,
                                        event_type=AuditEventType.BUDGET_VIOLATION,
                                        merchant_id=merchant.id,
                                        conversation_id=conversation.id,
                                        action="add_to_cart_budget_blocked",
                                        reasoning=f"Item addition blocked: ₹{projected_total:.0f} exceeds hard budget ₹{budget_cap:.0f}",
                                        input_data={"product": product.name, "additional_cost": additional_cost, "budget_limit": budget_cap},
                                        output_data={"blocked": True},
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
                                    reasoning=f"Added {qty}x {product.name} (₹{product.price}) to cart. Total: ₹{cart['total']}" + (f" (Remaining budget: ₹{budget_cap - cart['total']:.0f})" if budget_cap else ""),
                                )
                                if merchant:
                                    await log_audit_event(
                                        db=db,
                                        event_type=AuditEventType.AGENT_DECISION,
                                        merchant_id=merchant.id,
                                        conversation_id=conversation.id,
                                        action="add_to_cart",
                                        reasoning=f"Added {qty}x {product.name} (₹{product.price}) to cart. New total: ₹{cart['total']}",
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

                        tool_result = {
                            "success": len(items) < initial_len,
                            "remaining_items": len(items),
                            "cart_total": cart["total"],
                        }

                    elif fn_name == "view_cart":
                        tool_result = cart

                    elif fn_name == "clear_cart":
                        action_type = "cart_update"
                        cart["items"] = []
                        update_conversation_cart(conversation, cart)
                        cart = conversation.cart
                        tool_result = {"success": True, "cart": cart}

                    elif fn_name == "checkout_and_pay":
                        if not merchant:
                            tool_result = {"success": False, "error": "No store selected yet. Please select a store before checkout."}
                        else:
                            action_type = "checkout"
                            c_name = fn_args.get("customer_name")
                            c_phone = fn_args.get("customer_phone")

                            try:
                                order = await order_service.create_order_from_conversation(
                                    db=db,
                                    conversation_id=conversation.id,
                                    merchant_id=merchant.id,
                                    customer_name=c_name,
                                    customer_phone=c_phone,
                                )
                                payment_link = order.payment_link
                                tool_result = {
                                    "success": True,
                                    "order_id": str(order.id),
                                    "total": order.total,
                                    "payment_link": payment_link,
                                    "rzp_order_id": order.rzp_order_id,
                                }
                                add_agent_reasoning(
                                    conversation,
                                    action="checkout_and_pay",
                                    reasoning=f"Generated Razorpay Order #{str(order.id)[:8]} for ₹{order.total}. Payment link: {payment_link}",
                                )
                            except ValueError as budget_err:
                                logger.warning("Checkout blocked by budget guardrail: %s", budget_err)
                                tool_result = {"success": False, "guardrail_error": str(budget_err)}
                            except Exception as e:
                                logger.error("Checkout tool execution failed: %s", e)
                                tool_result = {"success": False, "error": str(e)}

                    # Append tool result back to llm_messages
                    llm_messages.append({
                        "role": "tool",
                        "tool_call_id": tool.id,
                        "name": fn_name,
                        "content": json.dumps(tool_result),
                    })

            if not final_text:
                final_text = "I have updated your request. What else would you like to add?"

        except Exception as exc:
            logger.error("CheckoutAgent error: %s", exc, exc_info=True)
            final_text = "I've processed your catalog request. How else can I assist with your order?"

        # Extract structured cart items for response
        cart_items_list = [
            CartItem(
                product_id=uuid.UUID(i["product_id"]) if isinstance(i["product_id"], str) else i["product_id"],
                name=i["name"],
                price=float(i["price"]),
                quantity=int(i.get("quantity", 1)),
            )
            for i in cart.get("items", [])
        ]

        # Save assistant message to conversation
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


checkout_agent = CheckoutAgent()
