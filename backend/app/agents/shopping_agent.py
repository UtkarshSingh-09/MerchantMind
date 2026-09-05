

"""Shopping Agent — Autonomous Single-Store Catalog Shopping, Smart Upselling & Razorpay Payments.
Manages customer carts, enforces budget guardrails with active alternatives, and completes Razorpay checkouts.
Supports real-time ReAct streaming of agent thinking, tool executions, and observations.
"""

import re
import json
import logging
import uuid
from typing import Any, AsyncGenerator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

STOPWORDS = {
    "hey", "hi", "hello", "please", "order", "me", "one", "two", "three", "four", "1", "2", "3", "4", "5",
    "i", "want", "to", "buy", "get", "need", "some", "a", "an", "the", "under",
    "below", "budget", "in", "for", "max", "rs", "rupees", "inr", "around", "approx",
    "can", "you", "show", "give", "and", "or", "with", "from", "of", "something", "like", "find"
}


SYNONYMS = {
    "belgium": "belgian",
    "choc": "chocolate",
    "veggie": "veg",
    "pastries": "pastry",
    "manchurian": "manchurian",
    "truffles": "truffle",
}


def extract_search_keywords(text: str) -> str:
    cleaned = re.sub(r"[^\w\s]", " ", text.lower())
    words = [SYNONYMS.get(w, w) for w in cleaned.split() if w not in STOPWORDS and not w.isdigit()]
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
from app.services import coupon_service
from app.schemas.chat import ProductRecommendation, CartItem, ChatResponse
from app.agents.discovery_agent import sanitize_english_response

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
            "name": "update_cart_quantity",
            "description": "Directly update the quantity of an item already in the cart (e.g. 'make it 3 dosas', 'change quantity to 2'). If quantity is set to 0, the item is removed.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_name": {"type": "string", "description": "Name or keyword of product in cart"},
                    "product_id": {"type": "string", "description": "UUID of product in cart if known"},
                    "new_quantity": {"type": "integer", "description": "New desired quantity (0 to remove)"},
                },
                "required": ["new_quantity"],
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
            "name": "apply_coupon",
            "description": "Apply a promotional coupon code (e.g. WELCOME10, FLAT50, SWEET20) to the customer's cart to receive a discount.",
            "parameters": {
                "type": "object",
                "properties": {
                    "coupon_code": {
                        "type": "string",
                        "description": "The coupon or promo code to apply",
                    },
                },
                "required": ["coupon_code"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_estimated_delivery_time",
            "description": "Check the estimated preparation time and delivery arrival window for the current cart from this merchant.",
            "parameters": {
                "type": "object",
                "properties": {
                    "delivery_address": {
                        "type": "string",
                        "description": "Optional customer delivery address or neighborhood in Bangalore",
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
            "description": "Create a Razorpay order and generate a secure payment link. ONLY call this after confirming fulfillment mode (pickup or delivery) and address with the customer.",
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
                    "delivery_address": {
                        "type": "string",
                        "description": "Complete delivery address including street, area, and 6-digit Bangalore pincode (e.g. 560038)",
                    },
                },
                "required": ["fulfillment_mode"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "track_order",
            "description": "View live tracking status, fulfillment details, and get the live tracking page link for the customer's order.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {"type": "string", "description": "Specific order ID if mentioned"}
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
    active_order: Any | None = None,
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

    active_order_section = ""
    if active_order:
        status_val = str(getattr(active_order, "status", "PAYMENT_LINK_SENT")).upper()
        is_paid = "PAID" in status_val or "CONFIRMED" in status_val
        active_order_section = f"""
ACTIVE ORDER STATUS & GROUND TRUTH:
- Order ID: {active_order.id}
- Order Total: ₹{active_order.total:.0f}
- Fulfillment: {active_order.fulfillment_mode}
- Payment Status: {'PAID & CONFIRMED' if is_paid else 'PAYMENT PENDING (NOT PAID YET)'}
- Secure Razorpay Link: {active_order.payment_link or 'N/A'}
- Live Tracking URL: /orders/{active_order.id}/tracking
"""

    return f"""You are ShoppingAgent in MerchantMind — the AI Shopping Concierge for '{merchant.name}'.
About the store: {merchant.description or 'Artisan & Specialty Store'}.
Store Location: {merchant.store_address or 'Bangalore, India'}
Currency: INR (₹).

CRITICAL LANGUAGE REQUIREMENT (STRICTLY MANDATORY):
- ALWAYS SPEAK AND RESPOND EXCLUSIVELY IN 100% CLEAR, NATURAL, ATTENTIVE ENGLISH.
- NEVER SPEAK IN HINDI, HINGLISH, URDU, OR CASUAL REGIONAL SLANG (NEVER use words like "Bhai", "yaar", "toh", "main", "seedha", "yeh lo", "chahiye", "accha", etc.).
- Keep all recommendations, checkout summaries, and greetings strictly in polished English.
- Failure to speak in pure English is strictly prohibited.
{memory_section}
{handoff_text}
{active_order_section}
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
5. **Conversational Checkout Workflow (MANDATORY)**:
When customer wants to checkout, buy, or pay (e.g. "checkout", "check out this", "pay", "order now", "buy this"):
DO NOT immediately call `checkout_and_pay` unless fulfillment mode and address are already confirmed! Follow this state machine:

- **STEP 1 (Fulfillment Choice)**:
  If the customer has NOT stated whether they want store pickup or doorstep delivery:
  Ask: "Would you like store pickup or doorstep delivery?"
  Include interactive options on their own line:
  [🛍️ Store Pickup] [🚚 Doorstep Delivery]

- **STEP 2A (If Customer Chooses Store Pickup)**:
  If customer chooses pickup (or says "pickup", "store pickup"):
  Immediately call `checkout_and_pay(fulfillment_mode="pickup")`.
  Confirm with:
  "Your pickup order is ready! 🛍️
  • Item: {cart_summary_str} — {merchant.name}
  • Total: ₹[amount]
  • Pickup: Store counter
  Please tap the payment button below to complete your order."

- **STEP 2B (If Customer Chooses Doorstep Delivery)**:
  If customer chooses delivery (or says "delivery", "doorstep"):
  Check if customer has a saved address in memory/profile (e.g. "Flat 402, 100 Feet Road, Indiranagar, Bangalore - 560038"):
  - If a saved address exists:
    Ask: "Would you like this delivered to your saved address at Flat 402, 100 Feet Road, Indiranagar, Bangalore - 560038, or a new address?"
    Include interactive options on their own line:
    [📍 Use Saved Address] [✏️ Enter New Address]
    - If customer confirms saved address (says "saved address", "same address", "yes", "indiranagar"):
      Call `checkout_and_pay(fulfillment_mode="delivery", delivery_address="Flat 402, 100 Feet Road, Indiranagar, Bangalore - 560038")`.
    - If customer says "new address" or wants to change:
      Ask: "Please share your delivery address."
  - If no saved address exists:
    Ask: "Please share your delivery address."

- **STEP 3 (Address & 6-Digit Pincode Validation for Delivery)**:
  When customer provides an address:
  Verify if it includes street/area and a 6-digit Bangalore pincode (e.g. 560xxx).
  - If pincode or area is missing (e.g. customer only says "MG Road" or "Flat 102"):
    Ask: "Got your address! Could you also provide your 6-digit Bangalore pincode and area for smooth delivery?"
  - Once full address with 6-digit pincode is provided:
    Call `checkout_and_pay(fulfillment_mode="delivery", delivery_address=full_address)`.

6. **STRICT SINGLE-STORE BOUNDARY & MISSING ITEM POLICY (MANDATORY)**:
- You represent ONLY '{merchant.name}'. You can ONLY add items that exist in '{merchant.name}'!
- When the customer asks to add an item (e.g. "also add one filter coffee", "add cold brew", "add samosa"):
  - Check if '{merchant.name}' has this item in its catalog.
  - If yes: Call `add_to_cart` and add it from '{merchant.name}'.
  - If '{merchant.name}' DOES NOT have this item:
    Politely and clearly explain:
    "We don't have [item] at {merchant.name}. On our menu, we have delicious options like [alternative 1] (₹XX) and [alternative 2] (₹XX)! Would you like to add one of these instead, or proceed with your current cart?"
  - NEVER add an item from another restaurant or pretend to have an item that is not in '{merchant.name}' catalog!

7. **STRICT PAYMENT INTEGRITY (NEVER HALLUCINATE PAYMENT CONFIRMATION)**:
- You are STRICTLY FORBIDDEN from declaring a payment successful or claiming money was received (e.g. "Your payment of ₹170 has been processed successfully! ✅") based solely on a user's text message (such as "pay now", "I paid", "make payment for me", "💳 Pay ₹170 Now", etc.).
- Customers must complete their payment on the secure Razorpay payment page.
- If the customer asks "can you make payment for me", "how to pay", "where to pay", or sends a pay request:
  Direct them to click their secure payment link:
  "Please complete your payment directly via Razorpay: [💳 Pay via Razorpay Secure]({getattr(active_order, 'payment_link', '') if active_order else ''})
  Once completed on Razorpay, your order will automatically be confirmed with your official receipt and live tracking!"
- NEVER invent fake pickup codes (e.g. AZZ-4821) or fake confirmation messages!

7. **LIVE ORDER TRACKING & ARRIVAL ALARM**:
- If customer asks to go to the tracking page or track their order (e.g. "go to tracking page", "can you go to the tracking page", "take me to tracking", "track my order", "show tracking", "track order"):
  Say warmly and concisely: "Okay! Taking you to your live tracking page now... 🚀\n\n[🚚 View Live Order Tracking]({f'/orders/{active_order.id}/tracking' if active_order else '/orders/tracking'})" so the frontend can redirect immediately.
- If customer asks to set an alarm when the order arrives or wake them up on delivery (e.g. "set an alarm when the order comes", "set alarm", "wake me when food arrives", "alert me on arrival"):
  Confirm warmly that their arrival alarm is armed! Provide the direct tracking link with the alarm parameter:
  "I have armed your arrival alarm! A loud chime will automatically ring the moment your delivery arrives: [🔔 Open Live Tracking & Armed Alarm]({f'/orders/{active_order.id}/tracking?alarm=true' if active_order else '/orders/tracking?alarm=true'})"

8. **Tone**: Warm, enthusiastic, concise, and helpful.
"""


def _format_cart_items_for_response(items: list[dict[str, Any]]) -> list[CartItem]:
    out: list[CartItem] = []
    for i in items:
        pid = i.get("product_id") or i.get("id")
        try:
            p_uuid = uuid.UUID(str(pid)) if pid else uuid.uuid4()
        except Exception:
            p_uuid = uuid.uuid4()
        p_price = float(i.get("price") or i.get("unit_price") or 0.0)
        out.append(
            CartItem(
                product_id=p_uuid,
                name=str(i.get("name", "Product")),
                price=p_price,
                quantity=int(i.get("quantity", 1)),
            )
        )
    return out


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
                            "merchant_id": str(merchant.id),
                            "merchant_name": merchant.name,
                        })
                    cart["items"] = items
                    cart["merchant_id"] = str(merchant.id)
                    cart["merchant_name"] = merchant.name
                    update_conversation_cart(conversation, cart)
                    cart = conversation.cart

                    tool_result = {
                        "success": True,
                        "added_product": product.name,
                        "quantity": qty,
                        "cart_total": cart["total"],
                        "cart_items": cart["items"],
                        "store_name": merchant.name,
                        "budget_remaining": (budget_cap - cart["total"]) if budget_cap else None,
                    }
                    add_agent_reasoning(
                        conversation,
                        action="add_to_cart",
                        reasoning=f"Added {qty}x {product.name} (₹{product.price:.0f}) from {merchant.name} to cart. Total: ₹{cart['total']:.0f}" + (f" (Remaining budget: ₹{budget_cap - cart['total']:.0f})" if budget_cap else ""),
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

        elif fn_name == "update_cart_quantity":
            action_type = "cart_update"
            pid = fn_args.get("product_id")
            pname = fn_args.get("product_name")
            new_qty = int(fn_args.get("new_quantity", 1))
            items = list(cart.get("items", []))

            target_idx = None
            for idx, it in enumerate(items):
                if pid and str(it.get("product_id")) == str(pid):
                    target_idx = idx
                    break
                elif pname and pname.lower() in it.get("name", "").lower():
                    target_idx = idx
                    break

            if target_idx is None:
                tool_result = {"success": False, "error": f"Item '{pname or pid}' was not found in your cart to update."}
            elif new_qty <= 0:
                removed_name = items[target_idx].get("name", "Item")
                items.pop(target_idx)
                cart["items"] = items
                update_conversation_cart(conversation, cart)
                cart = conversation.cart
                tool_result = {
                    "success": True,
                    "action": "removed",
                    "product_name": removed_name,
                    "cart_total": cart["total"],
                    "cart_items": cart["items"],
                    "message": f"Removed {removed_name} from your cart. New cart total: ₹{cart['total']:.0f}",
                }
                add_agent_reasoning(
                    conversation,
                    action="update_cart_quantity",
                    reasoning=f"Quantity set to 0. Removed {removed_name} from cart. Total: ₹{cart['total']:.0f}",
                )
            else:
                item = items[target_idx]
                old_qty = item.get("quantity", 1)
                unit_price = float(item.get("price", 0.0))
                current_total = float(cart.get("total", 0.0))
                cost_delta = (new_qty - old_qty) * unit_price
                projected_total = current_total + cost_delta

                budget_cfg = cart.get("budget") or {}
                budget_cap = budget_cfg.get("budget_amount")
                is_hard = budget_cfg.get("is_hard_limit", False)

                if is_hard and budget_cap and projected_total > budget_cap:
                    tool_result = {
                        "success": False,
                        "budget_blocked": True,
                        "message": f"Updating {item.get('name')} to {new_qty} brings total to ₹{projected_total:.0f}, exceeding your budget of ₹{budget_cap:.0f}.",
                    }
                else:
                    item["quantity"] = new_qty
                    cart["items"] = items
                    update_conversation_cart(conversation, cart)
                    cart = conversation.cart
                    tool_result = {
                        "success": True,
                        "action": "quantity_updated",
                        "product_name": item.get("name"),
                        "old_quantity": old_qty,
                        "new_quantity": new_qty,
                        "cart_total": cart["total"],
                        "cart_items": cart["items"],
                        "message": f"Updated '{item.get('name')}' quantity to {new_qty}. New cart total: ₹{cart['total']:.0f}",
                    }
                    add_agent_reasoning(
                        conversation,
                        action="update_cart_quantity",
                        reasoning=f"Updated {item.get('name')} from {old_qty} to {new_qty}. Cart total is now ₹{cart['total']:.0f}",
                    )

        elif fn_name == "apply_coupon":
            action_type = "cart_update"
            code = fn_args.get("coupon_code", "")
            coupon_res = coupon_service.apply_coupon_to_cart(coupon_code=code, cart=cart)
            if coupon_res.get("success"):
                cart = coupon_res["cart"]
                update_conversation_cart(conversation, cart)
                cart = conversation.cart
                add_agent_reasoning(
                    conversation,
                    action="apply_coupon",
                    reasoning=f"Applied coupon '{code.upper()}': Saved ₹{coupon_res.get('discount_amount', 0):.0f}. New total: ₹{cart['total']:.0f}",
                )
            tool_result = coupon_res

        elif fn_name == "get_estimated_delivery_time":
            deliv_addr = fn_args.get("delivery_address")
            eta_info = await order_service.estimate_delivery_time(
                db=db,
                merchant_id=merchant.id,
                items=cart.get("items", []),
                delivery_address=deliv_addr,
            )
            tool_result = eta_info
            add_agent_reasoning(
                conversation,
                action="estimated_delivery_time",
                reasoning=f"Calculated delivery ETA for {merchant.name}: {eta_info.get('delivery_window')} (Total ~{eta_info.get('total_estimated_minutes')} mins)",
            )

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

            if len(items) < initial_len:
                cart["items"] = items
                update_conversation_cart(conversation, cart)
                cart = conversation.cart
                tool_result = {"success": True, "removed": pname or pid, "cart_total": cart["total"]}
            else:
                tool_result = {"success": False, "error": f"Item '{pname or pid}' not found in cart."}

        elif fn_name == "view_cart":
            tool_result = cart

        elif fn_name == "clear_cart":
            action_type = "cart_update"
            cart["items"] = []
            cart["total"] = 0.0
            cart["merchant_id"] = None
            cart["merchant_name"] = None
            conversation.merchant_id = None
            update_conversation_cart(conversation, cart)
            cart = conversation.cart
            tool_result = {"success": True, "message": "Cart cleared and store unlinked. Customer can choose any store across Bangalore."}

        elif fn_name == "checkout_and_pay":
            action_type = "checkout"
            cname = fn_args.get("customer_name")
            cphone = fn_args.get("customer_phone")
            f_mode = fn_args.get("fulfillment_mode", "delivery")
            deliv_addr = fn_args.get("delivery_address")

            try:
                order = await order_service.create_order(
                    db=db,
                    merchant_id=merchant.id,
                    conversation_id=conversation.id,
                    customer_name=cname,
                    customer_phone=cphone,
                    fulfillment_mode=f_mode,
                    delivery_address=deliv_addr,
                )
                payment_link = order.payment_link
                # Reset conversation cart upon order creation
                cart["items"] = []
                cart["total"] = 0.0
                update_conversation_cart(conversation, cart)

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

        elif fn_name == "track_order":
            action_type = "tracking"
            order_id_arg = fn_args.get("order_id")
            from app.models.order import Order
            from sqlalchemy import select

            target_order = None
            if order_id_arg:
                try:
                    target_order = await db.get(Order, uuid.UUID(str(order_id_arg)))
                except Exception:
                    pass

            if not target_order:
                res = await db.execute(
                    select(Order)
                    .where(Order.conversation_id == conversation.id)
                    .order_by(Order.created_at.desc())
                    .limit(1)
                )
                target_order = res.scalar_one_or_none()

            if not target_order and conversation.customer_id:
                res = await db.execute(
                    select(Order)
                    .where(Order.customer_id == conversation.customer_id)
                    .order_by(Order.created_at.desc())
                    .limit(1)
                )
                target_order = res.scalar_one_or_none()

            if target_order:
                status_str = target_order.status.value if hasattr(target_order.status, "value") else str(target_order.status)
                tool_result = {
                    "success": True,
                    "order_id": str(target_order.id),
                    "status": status_str,
                    "fulfillment_mode": target_order.fulfillment_mode,
                    "total": target_order.total,
                    "tracking_url": f"/orders/{target_order.id}/tracking",
                    "store_name": merchant.name,
                    "instruction": f"Order #{str(target_order.id)[:8]} retrieved! Say: 'Okay! Taking you to your live tracking page now... 🚀\n\n[🚚 Open Live Order Tracking](/orders/{target_order.id}/tracking)' so the user is immediately redirected.",
                }
                add_agent_reasoning(
                    conversation,
                    action="track_order",
                    reasoning=f"Retrieved live tracking for Order #{str(target_order.id)[:8]}. Tracking link: /orders/{target_order.id}/tracking",
                )
            else:
                tool_result = {
                    "success": False,
                    "error": "No active order found for this session.",
                    "instruction": "Explain that no order was found yet, and invite the customer to order first.",
                }

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
                    conversation_id=conversation.id,
                    merchant_id=merchant.id,
                    merchant_name=merchant.name,
                    message=clarification_text,
                    cart=_format_cart_items_for_response(cart.get("items", [])),
                    cart_total=float(cart.get("total", 0.0)),
                    action="chat",
                )

            if resolved_edit.get("actions"):
                summary_ops = []
                for op in resolved_edit["actions"]:
                    if op["action"] == "remove":
                        cart_items = [i for i in cart.get("items", []) if str(i.get("product_id")) != str(op["product_id"])]
                        cart["items"] = cart_items
                        cart["total"] = sum(float(i.get("unit_price", 0)) * int(i.get("quantity", 1)) for i in cart_items)
                        summary_ops.append(f"• Removed **{op['name']}** from cart")
                    elif op["action"] == "clear":
                        cart["items"] = []
                        cart["total"] = 0.0
                        cart["merchant_id"] = None
                        cart["merchant_name"] = None
                        conversation.merchant_id = None
                        summary_ops.append("• Cleared all items from cart")
                    elif op["action"] == "update_qty":
                        existing = next((i for i in cart.get("items", []) if str(i.get("product_id")) == str(op["product_id"])), None)
                        if existing:
                            old_q = existing.get("quantity", 1)
                            new_q = int(op["quantity"])
                            existing["quantity"] = new_q
                            u_pr = float(existing.get("unit_price") or existing.get("price", 0))
                            summary_ops.append(f"• Updated **{op['name']}** quantity from {old_q} to **{new_q}** (₹{u_pr * new_q:.0f})")
                        else:
                            cart.setdefault("items", []).append({
                                "product_id": str(op["product_id"]),
                                "name": op["name"],
                                "unit_price": op["unit_price"],
                                "price": op["unit_price"],
                                "quantity": op["quantity"],
                                "merchant_id": str(merchant.id),
                                "merchant_name": merchant.name,
                            })
                            summary_ops.append(f"• Added **{op['quantity']}x {op['name']}** (₹{op['unit_price'] * op['quantity']:.0f})")
                    elif op["action"] == "add":
                        existing = next((i for i in cart.get("items", []) if str(i.get("product_id")) == str(op["product_id"])), None)
                        if existing:
                            existing["quantity"] = int(existing.get("quantity", 1)) + int(op["quantity"])
                        else:
                            cart.setdefault("items", []).append({
                                "product_id": str(op["product_id"]),
                                "name": op["name"],
                                "unit_price": op["unit_price"],
                                "price": op["unit_price"],
                                "quantity": op["quantity"],
                                "merchant_id": str(merchant.id),
                                "merchant_name": merchant.name,
                            })
                        summary_ops.append(f"• Added **{op['quantity']}x {op['name']}** (₹{op['unit_price'] * op['quantity']:.0f})")

                cart["merchant_id"] = str(merchant.id)
                cart["merchant_name"] = merchant.name
                cart["total"] = sum(float(i.get("unit_price") or i.get("price", 0)) * int(i.get("quantity", 1)) for i in cart.get("items", []))

                update_conversation_cart(conversation, cart)
                add_agent_reasoning(
                    conversation,
                    action="entity_resolution",
                    reasoning=f"Deterministically executed compound cart update: {', '.join(summary_ops)}",
                )
                ops_text = "\n".join(summary_ops) if summary_ops else f"• Verified items in your cart"
                final_msg = f"I've updated your order at **{merchant.name}**:\n{ops_text}\n\n🛒 **Cart Total: ₹{cart.get('total', 0):.0f}**\nWould you like to add anything else or proceed to checkout?"
                add_message_to_conversation(conversation, role="assistant", content=final_msg)
                return ChatResponse(
                    conversation_id=conversation.id,
                    merchant_id=merchant.id,
                    merchant_name=merchant.name,
                    message=final_msg,
                    cart=_format_cart_items_for_response(cart.get("items", [])),
                    cart_total=float(cart.get("total", 0.0)),
                    action="cart_update",
                )

        # Query active order for this conversation if any
        from app.models.order import Order
        active_order_res = await db.execute(
            select(Order)
            .where(Order.conversation_id == conversation.id)
            .order_by(Order.created_at.desc())
        )
        active_order = active_order_res.scalar_one_or_none()

        catalog_summary = await get_merchant_catalog_summary(db, merchant.id, limit=30)
        customer_mem = await build_customer_profile_memory(conversation.customer_id, db)
        system_prompt = _build_shopping_prompt(
            merchant=merchant,
            catalog_summary=catalog_summary,
            current_cart=cart,
            handoff_context=conversation.handoff_context,
            customer_memory=customer_mem,
            active_order=active_order,
        )

        # Autonomous Razorpay Payment Fast-Path for Active Orders
        u_clean = (user_message or "").lower().strip()
        is_pay_intent = any(k in u_clean for k in [
            "payment", "pay", "checkout", "to a payment", "do a payment", "do payment",
            "pay for me", "make payment", "proceed to pay", "open razorpay", "open payment"
        ])
        if (
            is_pay_intent
            and active_order
            and active_order.payment_link
            and "PAID" not in str(getattr(active_order, "status", "")).upper()
            and "CANCELLED" not in str(getattr(active_order, "status", "")).upper()
        ):
            order_total_val = float(getattr(active_order, "total", 0.0))
            order_id_str = str(active_order.id)
            pay_msg = (
                f"Opening secure Razorpay Checkout for your order (₹{order_total_val:.0f}) now! 💳\n\n"
                f"Please complete your payment on the secure Razorpay screen: [💳 Pay ₹{order_total_val:.0f} via Razorpay Secure]({active_order.payment_link})\n\n"
                f"Once confirmed on Razorpay, your order will automatically confirm and dispatch!"
            )
            add_message_to_conversation(
                conversation,
                role="assistant",
                content=pay_msg,
                metadata={
                    "action": "checkout",
                    "payment_link": active_order.payment_link,
                    "order_id": order_id_str,
                },
            )
            return ChatResponse(
                conversation_id=conversation.id,
                order_id=order_id_str,
                merchant_id=merchant.id,
                merchant_name=merchant.name,
                message=pay_msg,
                recommendations=None,
                cart=[],
                cart_total=0.0,
                action="checkout",
                payment_link=active_order.payment_link,
            )

        # Memory optimization: sliding window + summarization
        optimized_history = await build_optimized_context(conversation, max_recent=6)

        llm_messages: list[dict[str, Any]] = [
            {"role": "system", "content": system_prompt},
            *optimized_history,
        ]

        recommendations: list[ProductRecommendation] = []
        action_type = "chat"
        payment_link: str | None = (
            active_order.payment_link
            if active_order and "PAID" not in str(getattr(active_order, "status", "")).upper() and "CANCELLED" not in str(getattr(active_order, "status", "")).upper()
            else None
        )
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
                try:
                    synth_resp = await groq_client.chat_completion(
                        messages=llm_messages,
                        temperature=0.3,
                        max_tokens=450,
                    )
                    final_text = synth_resp.choices[0].message.content or ""
                except Exception as synth_err:
                    logger.warning("ShoppingAgent synthesis error: %s", synth_err)

            if not final_text:
                final_text = f"I've updated your order for {merchant.name}. Ready to checkout or explore more items?"

        except Exception as exc:
            logger.error("ShoppingAgent error: %s", exc, exc_info=True)
            final_text = "I've processed your store request. How else can I assist with your order?"

        final_text = sanitize_english_response(final_text)

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
                    "chat_response": ChatResponse(
                        conversation_id=conversation.id,
                        merchant_id=merchant.id,
                        merchant_name=merchant.name,
                        message=clarification_text,
                        recommendations=None,
                        cart=_format_cart_items_for_response(cart.get("items", [])),
                        cart_total=float(cart.get("total", 0.0)),
                        action="chat",
                        payment_link=None,
                    ).model_dump(mode="json"),
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
                        cart["total"] = sum(float(i.get("unit_price") or i.get("price", 0)) * int(i.get("quantity", 1)) for i in cart_items)
                        summary_ops.append(f"• Removed **{op['name']}** from cart")
                    elif op["action"] == "clear":
                        cart["items"] = []
                        cart["total"] = 0.0
                        cart["merchant_id"] = None
                        cart["merchant_name"] = None
                        conversation.merchant_id = None
                        summary_ops.append("• Cleared all items from cart")
                    elif op["action"] == "update_qty":
                        existing = next((i for i in cart.get("items", []) if str(i.get("product_id")) == str(op["product_id"])), None)
                        if existing:
                            old_q = existing.get("quantity", 1)
                            new_q = int(op["quantity"])
                            existing["quantity"] = new_q
                            u_pr = float(existing.get("unit_price") or existing.get("price", 0))
                            summary_ops.append(f"• Updated **{op['name']}** quantity from {old_q} to **{new_q}** (₹{u_pr * new_q:.0f})")
                        else:
                            cart.setdefault("items", []).append({
                                "product_id": str(op["product_id"]),
                                "name": op["name"],
                                "unit_price": op["unit_price"],
                                "price": op["unit_price"],
                                "quantity": op["quantity"],
                                "merchant_id": str(merchant.id),
                                "merchant_name": merchant.name,
                            })
                            summary_ops.append(f"• Added **{op['quantity']}x {op['name']}** (₹{op['unit_price'] * op['quantity']:.0f})")
                    elif op["action"] == "add":
                        existing = next((i for i in cart.get("items", []) if str(i.get("product_id")) == str(op["product_id"])), None)
                        if existing:
                            existing["quantity"] = int(existing.get("quantity", 1)) + int(op["quantity"])
                        else:
                            cart.setdefault("items", []).append({
                                "product_id": str(op["product_id"]),
                                "name": op["name"],
                                "unit_price": op["unit_price"],
                                "price": op["unit_price"],
                                "quantity": op["quantity"],
                                "merchant_id": str(merchant.id),
                                "merchant_name": merchant.name,
                            })
                        summary_ops.append(f"• Added **{op['quantity']}x {op['name']}** (₹{op['unit_price'] * op['quantity']:.0f})")

                cart["merchant_id"] = str(merchant.id)
                cart["merchant_name"] = merchant.name
                cart["total"] = sum(float(i.get("unit_price") or i.get("price", 0)) * int(i.get("quantity", 1)) for i in cart.get("items", []))

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
                ops_text = "\n".join(summary_ops) if summary_ops else f"• Verified items in your cart"
                final_msg = f"I've updated your order at **{merchant.name}**:\n{ops_text}\n\n🛒 **Cart Total: ₹{cart.get('total', 0):.0f}**\nWould you like to add anything else or proceed to checkout?"
                add_message_to_conversation(conversation, role="assistant", content=final_msg)
                yield {
                    "type": "answer",
                    "agent": "ShoppingAgent",
                    "content": final_msg,
                    "chat_response": ChatResponse(
                        conversation_id=conversation.id,
                        merchant_id=merchant.id,
                        merchant_name=merchant.name,
                        message=final_msg,
                        recommendations=None,
                        cart=_format_cart_items_for_response(cart.get("items", [])),
                        cart_total=float(cart.get("total", 0.0)),
                        action="cart_update",
                        payment_link=None,
                    ).model_dump(mode="json"),
                }
                return

        catalog_summary = await get_merchant_catalog_summary(db, merchant.id, limit=30)
        customer_mem = await build_customer_profile_memory(conversation.customer_id, db)

        # Check for active order on this conversation
        from app.models.order import Order, OrderStatus
        from sqlalchemy import select
        active_order_res = await db.execute(
            select(Order)
            .where(Order.conversation_id == conversation.id)
            .order_by(Order.created_at.desc())
            .limit(1)
        )
        active_order = active_order_res.scalar_one_or_none()

        system_prompt = _build_shopping_prompt(
            merchant=merchant,
            catalog_summary=catalog_summary,
            current_cart=cart,
            handoff_context=conversation.handoff_context,
            customer_memory=customer_mem,
            active_order=active_order,
        )

        optimized_history = await build_optimized_context(conversation, max_recent=6)

        llm_messages: list[dict[str, Any]] = [
            {"role": "system", "content": system_prompt},
            *optimized_history,
        ]

        recommendations: list[ProductRecommendation] = []
        action_type = "chat"
        tracked_order_id: str | None = None
        payment_link: str | None = (
            active_order.payment_link
            if active_order and "PAID" not in str(getattr(active_order, "status", "")).upper() and "CANCELLED" not in str(getattr(active_order, "status", "")).upper()
            else None
        )
        final_text = ""

        # 3.5 Autonomous Razorpay Payment Fast-Path for Active Orders
        u_clean = (user_message or "").lower().strip()
        is_pay_intent = any(k in u_clean for k in [
            "payment", "pay", "checkout", "to a payment", "do a payment", "do payment",
            "pay for me", "make payment", "proceed to pay", "open razorpay", "open payment"
        ])
        if is_pay_intent and active_order and payment_link:
            order_total_val = float(getattr(active_order, "total", 0.0))
            order_id_str = str(active_order.id)
            pay_msg = (
                f"Opening secure Razorpay Checkout for your order (₹{order_total_val:.0f}) now! 💳\n\n"
                f"Please complete your payment on the secure Razorpay screen: [💳 Pay ₹{order_total_val:.0f} via Razorpay Secure]({payment_link})\n\n"
                f"Once confirmed on Razorpay, your order will automatically confirm and dispatch!"
            )
            add_message_to_conversation(
                conversation,
                role="assistant",
                content=pay_msg,
                metadata={
                    "action": "checkout",
                    "payment_link": payment_link,
                    "order_id": order_id_str,
                },
            )
            chat_resp = ChatResponse(
                conversation_id=conversation.id,
                order_id=order_id_str,
                merchant_id=merchant.id,
                merchant_name=merchant.name,
                message=pay_msg,
                recommendations=None,
                cart=[],
                cart_total=0.0,
                action="checkout",
                payment_link=payment_link,
            )
            yield {
                "type": "answer",
                "agent": "ShoppingAgent",
                "content": pay_msg,
                "chat_response": chat_resp.model_dump(mode="json"),
            }
            return

        # 3.6 Autonomous Live Order Tracking Fast-Path
        is_tracking_intent = any(k in u_clean for k in [
            "tracking page", "show me the tracking", "show tracking", "go to tracking",
            "track order", "track my order", "order tracking", "where is my order",
            "live tracking", "track my food", "tracking", "take me to tracking",
            "bring me to tracking", "open tracking"
        ]) or (
            re.search(r"\b(track|tracking)\b", u_clean) is not None
            and any(w in u_clean for w in ["go", "open", "show", "view", "page", "my", "where", "status"])
        )

        if is_tracking_intent:
            found_order = active_order
            if not found_order:
                # 1. Search by conversation_id
                res = await db.execute(
                    select(Order)
                    .where(Order.conversation_id == conversation.id)
                    .order_by(Order.created_at.desc())
                    .limit(1)
                )
                found_order = res.scalar_one_or_none()
            if not found_order and conversation.customer_id:
                # 2. Search by customer_id
                res = await db.execute(
                    select(Order)
                    .where(Order.customer_id == conversation.customer_id)
                    .order_by(Order.created_at.desc())
                    .limit(1)
                )
                found_order = res.scalar_one_or_none()
            if not found_order:
                # 3. Extract order UUID from conversation message history
                for m in reversed(conversation.messages or []):
                    c = m.get("content", "")
                    m_uuid = re.search(r"/orders/([0-9a-fA-F-]{36})/tracking", c) or re.search(r"([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})", c)
                    if m_uuid:
                        try:
                            import uuid as _uuid
                            ord_uuid = _uuid.UUID(m_uuid.group(1))
                            res = await db.execute(select(Order).where(Order.id == ord_uuid))
                            found_order = res.scalar_one_or_none()
                            if found_order:
                                break
                        except Exception:
                            pass
            if not found_order:
                # 4. Fallback to latest Order overall in the database
                res = await db.execute(
                    select(Order)
                    .order_by(Order.created_at.desc())
                    .limit(1)
                )
                found_order = res.scalar_one_or_none()

            if found_order:
                status_str = found_order.status.value if hasattr(found_order.status, "value") else str(found_order.status)
                tracking_url = f"/orders/{found_order.id}/tracking"
                tracking_msg = (
                    f"Okay! Taking you to your live tracking page for **Order #{str(found_order.id)[:8]}** now... 🚀\n\n"
                    f"• **Status:** {status_str}\n"
                    f"• **Fulfillment:** {found_order.fulfillment_mode.title()}\n"
                    f"• **Total:** ₹{found_order.total:.0f}\n\n"
                    f"[🚚 Open Live Order Tracking Dashboard]({tracking_url})"
                )
                add_message_to_conversation(conversation, role="assistant", content=tracking_msg)
                yield {
                    "type": "answer",
                    "agent": "ShoppingAgent",
                    "content": tracking_msg,
                    "chat_response": ChatResponse(
                        conversation_id=conversation.id,
                        order_id=str(found_order.id),
                        merchant_id=found_order.merchant_id or merchant.id,
                        merchant_name=merchant.name,
                        message=tracking_msg,
                        recommendations=None,
                        cart=[],
                        cart_total=0.0,
                        action="tracking",
                        payment_link=found_order.payment_link if "PAID" not in status_str.upper() else None,
                    ).model_dump(mode="json"),
                }
                return

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
                    if fn_name == "track_order" and t_res.get("order_id"):
                        tracked_order_id = str(t_res.get("order_id"))

                    # Summarize tool observation for ReAct stream
                    summary = ""
                    if fn_name == "search_catalog":
                        summary = f"Found {t_res.get('found_count', 0)} matching products in {merchant.name}"
                    elif fn_name == "add_to_cart":
                        if t_res.get("budget_blocked"):
                            summary = f"⚠️ Budget guardrail blocked addition: total would reach ₹{t_res.get('projected_total')} > limit ₹{t_res.get('budget_limit')}"
                        else:
                            summary = f"✅ Added to cart. New Total: ₹{t_res.get('cart_total', 0)}"
                    elif fn_name == "update_cart_quantity":
                        if t_res.get("budget_blocked"):
                            summary = f"⚠️ Budget guardrail blocked quantity update: limit exceeded"
                        else:
                            summary = f"🔄 {t_res.get('message', 'Updated quantity in cart')}"
                    elif fn_name == "apply_coupon":
                        if t_res.get("success"):
                            summary = f"🎉 Applied '{t_res.get('coupon_code')}': Saved ₹{t_res.get('discount_amount', 0):.0f} (Total: ₹{t_res.get('new_total', 0):.0f})"
                        else:
                            summary = f"⚠️ Coupon not applied: {t_res.get('error')}"
                    elif fn_name == "get_estimated_delivery_time":
                        summary = f"⏱️ Delivery ETA: {t_res.get('delivery_window')} (~{t_res.get('total_estimated_minutes')} mins total)"
                    elif fn_name == "get_upsell_suggestions":
                        summary = f"Found {t_res.get('suggested_count', 0)} complementary upsell pairings"
                    elif fn_name == "checkout_and_pay":
                        summary = f"💳 Generated Razorpay payment link for ₹{t_res.get('order_total', 0)}"
                    elif fn_name == "track_order":
                        summary = f"🚚 Retrieved live tracking for Order #{str(t_res.get('order_id', ''))[:8]}"
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
                try:
                    synth_resp = await groq_client.chat_completion(
                        messages=llm_messages,
                        temperature=0.3,
                        max_tokens=450,
                    )
                    final_text = synth_resp.choices[0].message.content or ""
                except Exception as synth_err:
                    logger.warning("ShoppingAgent streaming synthesis error: %s", synth_err)

            if not final_text:
                final_text = f"I've updated your order for {merchant.name}. Ready to checkout or explore more items?"

        except Exception as exc:
            logger.error("ShoppingAgent streaming error: %s", exc, exc_info=True)
            final_text = "I've processed your store request. How else can I assist with your order?"

        final_text = sanitize_english_response(final_text)

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
            order_id=str(active_order.id) if active_order else tracked_order_id,
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
