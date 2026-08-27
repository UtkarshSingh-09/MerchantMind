"""Checkout & Growth Agent powered by Groq with smart upselling, Razorpay payment flow, and Audit Guardrails."""

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
    get_merchant_catalog_summary,
)
from app.services.upsell_engine import get_upsell_suggestions
from app.services.conversation_service import (
    add_message_to_conversation,
    update_conversation_cart,
    add_agent_reasoning,
)
from app.services.audit_service import log_audit_event, AuditEventType
from app.services import order_service
from app.schemas.chat import ProductRecommendation, CartItem, ChatResponse

logger = logging.getLogger(__name__)

# Tools definition for Groq function calling
AGENT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_catalog",
            "description": "Search products in the merchant catalog by keyword, category, or price range.",
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


def _build_system_prompt(merchant: Merchant, catalog_summary: list[dict[str, Any]], current_cart: dict[str, Any]) -> str:
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
1. **Product Recommendation with Reasoning**: When customers ask for items (e.g. "I want a chocolate cake under ₹800"), search the catalog or pick from catalog overview. ALWAYS explain WHY you recommend each item (e.g., "Belgian chocolate layers with rich ganache, fits well within your ₹800 budget").
2. **Proactive Smart Upselling & Cross-Selling**:
   - Whenever an item is added to cart, call `get_upsell_suggestions` to discover natural pairings!
   - Examples: If customer adds a Birthday Cake, suggest: "Would you like to complete the celebration with our Birthday Candles Set (₹50) or Balloon Combo (₹150)?"
   - If customer adds Pastries or Breads, suggest a freshly brewed Artisan Coffee or Cold Beverage!
   - ALWAYS explain the reasoning for your upsell (e.g. occasion completeness, complementary flavors).
3. **Respect Customer Budget (Hard Guardrail)**: NEVER recommend items exceeding customer's stated budget. If cart is ₹650 and budget is ₹800, remaining budget is ₹150 — only recommend add-ons ≤ ₹150! If the cart exceeds stated budget, alert customer before checkout.
4. **Cart Actions**: Call `add_to_cart` or `remove_from_cart` when customer asks to add/buy/remove items.
5. **Checkout & Payment**: When customer wants to checkout, proceed to payment, or buy the cart items, call `checkout_and_pay` tool. Present the generated payment link clearly.
6. **Tone**: Warm, enthusiastic, concise, and conversion-focused. Format prices cleanly like `₹650`.
"""


class CheckoutAgent:
    """Agent orchestrating conversational commerce, smart upselling, Razorpay checkout, and audit logging."""

    async def process_message(
        self,
        db: AsyncSession,
        merchant: Merchant,
        conversation: Conversation,
        user_message: str,
    ) -> ChatResponse:
        """Process incoming customer message, execute tools iteratively, and return structured response."""
        # 1. Fetch catalog summary & current cart
        catalog_summary = await get_merchant_catalog_summary(db, merchant.id, limit=25)
        cart = conversation.cart or {"items": [], "total": 0.0}

        # 2. Add user message to conversation history
        add_message_to_conversation(conversation, role="user", content=user_message)

        # 3. Assemble LLM prompt messages
        system_prompt = _build_system_prompt(merchant, catalog_summary, cart)
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

        try:
            # Multi-turn tool execution loop (max 3 cycles)
            for _ in range(3):
                response = await groq_client.chat_completion(
                    messages=llm_messages,
                    tools=AGENT_TOOLS,
                    tool_choice="auto",
                    temperature=0.3,
                )
                response_msg = response.choices[0].message
                tool_calls = getattr(response_msg, "tool_calls", None)

                if not tool_calls:
                    final_text = response_msg.content or "How may I assist you further?"
                    break

                # Append assistant message with tool calls
                llm_messages.append(response_msg)

                # Process each tool call
                for tool in tool_calls:
                    fn_name = tool.function.name
                    try:
                        fn_args = json.loads(tool.function.arguments or "{}")
                    except Exception:
                        fn_args = {}

                    tool_result: dict[str, Any] = {}
                    logger.info("Executing tool %s with args %s", fn_name, fn_args)

                    if fn_name == "search_catalog":
                        action_type = "recommend"
                        query = fn_args.get("query")
                        category = fn_args.get("category")
                        min_p = fn_args.get("min_price")
                        max_p = fn_args.get("max_price")

                        found_products = await search_products(
                            db,
                            merchant.id,
                            query=query,
                            category=category,
                            min_price=min_p,
                            max_price=max_p,
                            limit=5,
                        )
                        tool_result = {
                            "found_count": len(found_products),
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
                                        reasoning=f"Matches your search criteria for ₹{p.price}",
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
                            }
                            add_agent_reasoning(
                                conversation,
                                action="add_to_cart",
                                reasoning=f"Added {qty}x {product.name} (₹{product.price}) to cart. Total: ₹{cart['total']}",
                            )
                            await log_audit_event(
                                db=db,
                                event_type=AuditEventType.AGENT_DECISION,
                                merchant_id=merchant.id,
                                conversation_id=conversation.id,
                                action="add_to_cart",
                                reasoning=f"Added {qty}x {product.name} (₹{product.price}) to cart. New cart total: ₹{cart['total']}",
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
            message=final_text,
            recommendations=recommendations if recommendations else None,
            cart=cart_items_list if cart_items_list else None,
            cart_total=float(cart.get("total", 0.0)),
            action=action_type,
            payment_link=payment_link,
        )


checkout_agent = CheckoutAgent()
