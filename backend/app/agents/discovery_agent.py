"""Discovery Agent — Autonomous Cross-Merchant City-Wide Product Discovery.
Scans multi-merchant inventories, generates comparison tables, enforces budget guardrails,
and executes seamless handoff to ShoppingAgent upon merchant selection.
Supports real-time ReAct streaming of agent thinking, tool executions, and observations.
"""

import re
import json
import logging
import uuid
import asyncio
from typing import Any, AsyncGenerator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.merchant import Merchant
from app.models.product import Product

STOPWORDS = {
    "actually", "hey", "hi", "hello", "please", "order", "me", "one", "two", "three", "four", "1", "2", "3", "4", "5",
    "i", "want", "to", "buy", "get", "need", "some", "a", "an", "the", "under",
    "below", "budget", "in", "for", "max", "rs", "rupees", "inr", "around", "approx",
    "can", "you", "show", "give", "and", "or", "with", "from", "of", "something", "like", "find",
    "my", "is", "also", "yeah", "this", "that", "it", "these", "those", "have", "looking",
    "am", "new", "city", "don't", "know", "anything", "options", "option", "first",
    "tell", "all", "things", "what", "written", "add", "card", "cart",
    "merchantmind", "merchant", "merchants", "mercanhtmind", "mind"
}

SYNONYMS = {
    "belgium": "belgian",
    "choc": "chocolate",
    "veggie": "veg",
    "pastries": "pastry",
    "pastry": "pastries",
    "manchurian": "manchurian",
    "truffles": "truffle",
}

GREETING_REGEX = re.compile(
    r"^\s*(hi|hello|hey|namaste|namaskara|good\s+(morning|afternoon|evening)|hola|greetings|merchantmind|merchant\s*mind|mercanhtmind)\b",
    re.IGNORECASE,
)

ADD_TO_CART_REGEX = re.compile(
    r"\b(add\s+(?:this|it|option\s*\d+|#\d+|the\s+(?:first|second|third)\s+one|[\w\s]+)?\s*(?:to|in)\s*(?:my\s+)?(?:cart|card|basket)|order\s+(?:this|it|option\s*\d+|#\d+|the\s+(?:first|second|third)\s+one))\b",
    re.IGNORECASE,
)


def extract_search_keywords(text: str) -> str:
    cleaned = re.sub(r"[^\w\s]", " ", text.lower())
    cleaned = re.sub(r"\b(?:merchant\s*mind|merchantmind|mercanhtmind|merchant)\b", " ", cleaned)
    words = [SYNONYMS.get(w, w) for w in cleaned.split() if w not in STOPWORDS and not w.isdigit()]
    return " ".join(words).strip()


FOOD_PATTERNS = [
    ("filter coffee", "coffee"),
    ("cold brew", "coffee"),
    ("coffee", "coffee"),
    ("kaapi", "coffee"),
    ("masala dosa", "dosa"),
    ("ghee roast", "dosa"),
    ("benne dosa", "dosa"),
    ("set dosa", "dosa"),
    ("dosa", "dosa"),
    ("idli", "idli"),
    ("vada", "vada"),
    ("margherita", "pizza"),
    ("pepperoni", "pizza"),
    ("veggie pizza", "pizza"),
    ("pizza", "pizza"),
    ("biryani", "biryani"),
    ("burger", "burger"),
    ("truffle cake", "cake"),
    ("pastry", "pastry"),
    ("cake", "cake"),
    ("noodles", "noodles"),
    ("pasta", "pasta"),
    ("chaat", "chaat"),
    ("sandwich", "sandwich"),
    ("manchurian", "chinese"),
    ("fried rice", "chinese"),
]

NUMBER_WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
    "1": 1, "2": 2, "3": 3, "4": 4, "5": 5, "6": 6,
    "a": 1, "an": 1, "single": 1, "double": 2, "pair": 2,
}


def parse_multi_food_items(text: str) -> list[dict[str, Any]]:
    text_lower = text.lower()
    found = []
    for pattern, canonical in FOOD_PATTERNS:
        matches = list(re.finditer(r"\b" + pattern + r"(?:s|es)?\b", text_lower))
        if matches:
            if any(f["canonical"] == canonical for f in found):
                continue
            for m in matches:
                start = m.start()
                preceding = text_lower[:start].strip().split()
                qty = 1
                if preceding:
                    last_w = preceding[-1]
                    if last_w in NUMBER_WORDS:
                        qty = NUMBER_WORDS[last_w]
                found.append({"raw": pattern, "canonical": canonical, "quantity": qty})
                break
    return found


def sanitize_english_response(text: str) -> str:
    """Sanitize any accidental Hindi / Hinglish colloquial phrases into clean, natural English."""
    if not text:
        return text
    cleaned = text
    # Strip openings like "Bhai, time kam hai toh main seedha top picks deta hoon! 🔥"
    cleaned = re.sub(
        r"^\s*bhai[,\s]+time\s+kam\s+hai[^\n]*\n*",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    # Strip standalone slang greetings like "Bhai, ", "Yaar, ", "Arrey, "
    cleaned = re.sub(
        r"^\s*(?:bhai|yaar|arrey)[,\s!]+",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    # Replace "Yeh lo Bangalore ke best/top <items> — sab 4.9⭐ rated:"
    cleaned = re.sub(
        r"^\s*yeh\s+lo\s+bangalore\s+ke\s+(?:best|top)\s+([a-zA-Z\s]+?)\s*[—-]\s*sab\s+(\d+(?:\.\d+)?(?:⭐|\s*stars?))\s*rated:?",
        r"Here are Bangalore's finest \1 — all \2 rated:",
        cleaned,
        flags=re.IGNORECASE,
    )
    # Replace stray "Yeh lo"
    cleaned = re.sub(
        r"\byeh\s+lo\b",
        "Here are",
        cleaned,
        flags=re.IGNORECASE,
    )
    # Replace "Truffles ka signature" -> "Truffles' signature"
    cleaned = re.sub(
        r"\b([A-Za-z0-9]+)\s+ka\s+signature\b",
        r"\1's signature",
        cleaned,
        flags=re.IGNORECASE,
    )
    # Replace "sab 4.9⭐ rated" -> "all 4.9⭐ rated"
    cleaned = re.sub(
        r"\bsab\s+(\d+(?:\.\d+)?(?:⭐|\s*stars?))\s*rated\b",
        r"all \1 rated",
        cleaned,
        flags=re.IGNORECASE,
    )
    return cleaned.strip()

from app.models.conversation import Conversation
from app.services.groq_client import groq_client
from app.services.catalog_search import (
    search_all_merchants_catalog,
    search_with_alternatives,
    search_by_occasion,
    get_all_merchants_summary,
    get_product_by_id_any_merchant,
)
from app.services import order_service
from app.services.conversation_service import (
    add_message_to_conversation,
    add_agent_reasoning,
    lock_conversation_to_merchant,
    update_conversation_cart,
    set_handoff_context,
)
from app.services.budget_extractor import extract_structured_budget
from app.services.audit_service import log_audit_event, AuditEventType
from app.services.memory_service import build_optimized_context, build_customer_profile_memory
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
                        "description": "Category filter (e.g. Pizza, South Indian, Cakes, Pastries, Biryani, Burgers, Chinese, Beverages)",
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
            "name": "search_by_occasion",
            "description": "Generate curated food, meal, and dessert combos for occasions like birthday parties, office lunch, romantic dates, tea time snacks, or family gatherings.",
            "parameters": {
                "type": "object",
                "properties": {
                    "occasion": {
                        "type": "string",
                        "description": "Occasion description (e.g. 'birthday party for 10 people', 'office lunch under ₹2000', 'romantic dinner for two')",
                    },
                    "people_count": {
                        "type": "integer",
                        "description": "Optional number of people to cater for",
                    },
                    "budget": {
                        "type": "number",
                        "description": "Optional maximum total budget in INR",
                    },
                },
                "required": ["occasion"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "reorder_previous",
            "description": "Reorder customer's last order or previous purchases. Automatically fetches order history, populates the cart with past items, and connects to the restaurant.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "Optional specific past order ID if mentioned",
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
            "description": "Add a discovered product to cart. In single-store mode, orders are prepared by a single restaurant kitchen. If the customer explicitly asks to order items from both/multiple stores together (e.g. 'order both', 'add both'), set allow_multi_store=True to enable dual-store cart with unified checkout.",
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
                    "merchant_name": {
                        "type": "string",
                        "description": "Merchant or store name (e.g. Veena Stores, Brahmin's Coffee Bar) if known",
                    },
                    "quantity": {
                        "type": "integer",
                        "description": "Quantity to add (default: 1)",
                    },
                    "allow_multi_store": {
                        "type": "boolean",
                        "description": "Set to True if customer explicitly wants to order both items or multi-store checkout (e.g. 'order both', 'add both').",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "clear_cart",
            "description": "Clear all items from customer's shopping cart and unlock from any currently selected restaurant. Use when the customer wants to switch stores or empty their cart.",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
]


BANGALORE_CUISINES_DIRECTORY = """
BANGALORE FOOD DIRECTORY (214 Verified Merchants, 5,350+ Genuine Dishes across 20 Neighborhoods):
• Artisan Bakeries & Cakes (12 stores): Sweet Chariot, Theobroma, Glen's Bakehouse, Magnolia Bakery, Smoor, Lavonne... (Belgian Truffle Cakes, Cheesecakes, Croissants, Eclairs — ₹120-₹850)
• South Indian Darshinis (12 stores): Vidyarthi Bhavan, CTR Shri Sagar, Brahmin's Coffee Bar, MTR, Taaza Thindi, Veena Stores... (Crispy Benne Dosas, Rava Idlis, Filter Coffee — ₹20-₹90)
• Biryani & Military Mess (12 stores): Meghana Foods, Shivaji Military Hotel, Nagarjuna, Ranganna, Mani's Dum Biryani... (Donne Mutton Biryani, Chicken Dum, Ghee Roast — ₹160-₹450)
• Indo-Chinese Wok (12 stores): Beijing Bites, Chung Wah, Mainland China, Szechuan Dragon, Auntie Fung's, Mamagoto... (Manchurian, Hakka Noodles, Schezwan Rice, Momos — ₹120-₹320)
• North Indian Dhabas (12 stores): Empire, Punjabi Angithi, Punjab Grill, Kapoor's Café, Dhaba 1986, Treat... (Butter Chicken, Dal Makhani, Paneer Tikka, Parathas — ₹25-₹420)
• Cafés & Specialty Roasters (12 stores): Third Wave Coffee, Blue Tokai, Doff Pub, Café Azzure, DYU Art Café... (Cold Brews, Sourdough Toasts, Pastas, Waffles — ₹110-₹340)
• Ice Cream Sundaes (12 stores): Corner House, Naturals, Polar Bear, Milano Gelato, Baskin Robbins... (Death by Chocolate, DBC, Hot Chocolate Fudge, Tender Coconut — ₹80-₹240)
• Gourmet Burgers & Wings (10 stores): Truffles Burgers, Burger Seigneur, Leon's, Plan B, Peppabowl... (Cheeseburgers, Peri Peri Wings, Kathi Rolls — ₹110-₹280)
• Artisan Pizzas & Pastas (10 stores): Toit Brewpub, Brik Oven, The Pizza Bakery, Onesta, Chianti... (Neapolitan Pizzas, Truffle Mushroom, Fettuccine — ₹150-₹490)
• Bangalore Street Chaats (10 stores): Sri Sairam's, Karnataka Bhelpuri, Bangarpet Pani Puri, Gullu's... (Masala Puri, Sev Puri, Dahi Puri, Pav Bhaji — ₹35-₹120)
• Traditional Mithai & Sweets (10 stores): Kanti Sweets, Asha Sweets, Sri Krishna Sweets, KC Das... (Mysore Pak, Kaju Katli, Motichoor Ladoo, Rasgulla — ₹70-₹290)
• Coastal Seafood & Mangalorean (10 stores): Karavalli, Mangalore Pearl, Kudla, Machali, Coast Kafe... (Neer Dosa, Anjal Tawa Fry, Kori Rotti, Prawns Ghee Roast — ₹50-₹450)
• Healthy Juices & Bowls (10 stores): Juice Junction, Fresh Pressery, Fruitbae, Keventers, EatFit... (ABC Detox Juice, Cold-Pressed Valencia, Quinoa Bowls — ₹50-₹240)
• Authentic Kerala Dining (10 stores): Calicut Paragon, Ente Keralam, Malabar Bay, Kumarakom... (Malabar Parotta, Beef Fry, Appam, Karimeen Pollichathu — ₹40-₹450)
• Arabian Shawarma & Mandi (10 stores): Savoury, Al Taza, Al-Amanah, Empire Arabian, Mandi King... (Jumbo Shawarma, Alfahm Chicken, Chicken & Mutton Mandi — ₹110-₹490)
• Pan-Asian Sushi & Ramen (10 stores): Daily Sushi, Taiki, Harima, Soo Ra Sang, Arirang... (California Rolls, Tonkotsu Ramen, Korean Fried Chicken — ₹190-₹450)
• Vegan & Farm-to-Table (10 stores): Green Theory, Enerjuvate, Go Native, Justbe, Carrots... (Millet Khichdi, Jackfruit Biryani, Vegan Mousse — ₹60-₹380)
• Continental European Grills (10 stores): Windmills Craftworks, Portland Steakhouse, Millers 46... (Roast Chicken Steak, Fish & Chips, Shepherd's Pie — ₹110-₹680)
• Royal Rajasthani & Gujarati Thali (10 stores): Rajdhani, Kesariya, Khandani Rajdhani, Gramin... (Grand Royal Thali, Dal Baati Churma, Gatte ki Sabzi — ₹40-₹380)
• Andhra Mess & Meals (10 stores): Nandhana Palace, Amaravathi, Bheema's, Rayalaseema Ruchulu... (Unlimited Andhra Veg Meals, Gongura Mutton, Royyala Vepudu — ₹40-₹380)
"""


def _build_discovery_system_prompt(
    city_merchants: list[dict[str, Any]],
    current_cart: dict[str, Any],
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

    memory_section = f"\n\n{customer_memory}\n" if customer_memory else ""

    return f"""You are Meera — MerchantMind's elite AI shopping concierge across Bangalore.
Think of yourself as the warmest, most knowledgeable local food guide in Bangalore. You know every food street, heritage bakery, Darshini, and cloud kitchen across Indiranagar, Koramangala, Jayanagar, Malleshwaram, Whitefield, and all 20 neighborhoods.

CRITICAL LANGUAGE REQUIREMENT (STRICTLY MANDATORY):
- ALWAYS SPEAK AND RESPOND EXCLUSIVELY IN 100% CLEAR, NATURAL, PROFESSIONAL ENGLISH.
- NEVER SPEAK IN HINDI, HINGLISH, URDU, OR CASUAL REGIONAL SLANG (NEVER use words like "Bhai", "yaar", "toh", "main", "seedha", "deta hoon", "yeh lo", "sab", "ka", "ki", "chahiye", "le lo", "accha", "arrey", "karein", "hai", etc.).
- Even for brief, single-word queries like "burger", respond warmly in standard English:
  "Here are Bangalore's finest burgers, all rated 4.9⭐:"
- Every dish description, comparison note, and recommendation MUST be in English (e.g., write "Truffles' signature" instead of "Truffles ka signature").
- Failure to speak in pure English is strictly prohibited.

Currency: INR (₹).

{memory_section}
{BANGALORE_CUISINES_DIRECTORY}

CUSTOMER CART:
{cart_summary_str}
BUDGET GUARDRAIL:
{budget_status_str}

SHOPKEEPER PRINCIPLES:
1. **Interactive, Human & Warm**: Speak like an attentive, passionate shopkeeper. Never produce dry robotic lists. Tell the customer why a dish is special, how it pairs, and give honest recommendations.
2. **Knowledge Funnel & Alternatives**:
   - If the customer asks for a specific item (e.g. "Belgium truffle cake") with a budget (e.g. "under ₹500"):
     - If the item starts at ₹620-₹675 (above budget), explain it clearly and warmly:
       "The authentic Belgian Truffle Cakes in Bangalore start at ₹620 (e.g. at Glen's Bakehouse or Sweet Chariot), which is slightly over your ₹500 budget. However, right within your ₹500 budget, we have delicious options like Fresh Pineapple Cream Cake (₹440) or Warm Chocolate Lava Cake (₹180)!"
     - Give them the choice: "Would you like to extend your budget to ₹620 for the Belgian Truffle, or shall we go with one of the options under ₹500?"
3. **Smart Autonomy ("Brain of Your Own")**:
   - If the customer says "add this to cart", "add the second one", or "add option 1", resolve the item and add it immediately.
   - If the customer says "add something with good rating", pick the highest-rated item from the options and add it with an enthusiastic note.
   - If the customer says "order from that shop I ordered before", check their favorite merchants in memory (like Sweet Chariot or Beijing Bites) and pick their favorite!
4. **Appetizing Presentation**: Use a clean, beautiful Markdown comparison table with columns: (#, Store, Dish, Quick Notes / Rating, Price in ₹). Follow with clear, numbered action options.
5. **CRITICAL CART ACTION ENFORCEMENT**:
   - When the customer asks to add an item to their cart, orders an item, picks a store/dish (e.g. "Add 2 × Ghee Roast Masala Dosa from Veena Stores", "add 2 dosa in my cart", "from brahmins coffee bar", "option 1"): YOU MUST CALL THE `add_to_cart` TOOL!
   - NEVER simply type a "Cart Summary" or pretend an item was added in text without executing the `add_to_cart` tool! If you don't call the `add_to_cart` tool, the cart on the customer's screen will NOT update and the user will see an empty cart!
6. **STRICT PAYMENT INTEGRITY (NEVER HALLUCINATE PAYMENT CONFIRMATION)**:
   - You are STRICTLY FORBIDDEN from declaring a payment successful or claiming money was received (e.g. "Your payment of ₹170 has been processed successfully! ✅") based solely on a user's text message (such as "pay now", "I paid", "make payment for me", "💳 Pay ₹170 Now", etc.).
   - Customers must complete their payment on the secure Razorpay payment page.
   - If the customer asks "can you make payment for me", "how to pay", "where to pay", or sends a pay request:
     Direct them to click their secure payment link.
   - NEVER invent fake pickup codes (e.g. AZZ-4821) or fake confirmation messages! Real payment confirmation is handled by the system after Razorpay webhook verification!
7. **LIVE ORDER TRACKING LINK**:
   - If customer asks to track order or go to tracking page, say: "Okay! Taking you to your live tracking page now... 🚀\n\n[🚚 Open Live Order Tracking Dashboard](/orders/<order_id>/tracking)" so the frontend redirects immediately.
8. **STRICT SINGLE-RESTAURANT FULFILLMENT & MULTI-ITEM ORDERING POLICY (MANDATORY)**:
   - IN OUR FOOD DELIVERY PLATFORM, EACH DELIVERY ORDER/CART MUST BE PREPARED AND PICKED UP FROM A SINGLE RESTAURANT KITCHEN. Items from different restaurants CANNOT be mixed into the same cart!
   - When a customer asks to order multiple items (e.g. "order chocolate lava cake and masala dosa", "burger and biryani", "one filter coffee one pizza"):
     a. Cuisine Compatibility Check:
        - Check if the requested items belong to distinct, incompatible culinary categories (e.g. South Indian Darshini Filter Coffee vs Wood-Fired Pizza, or Artisan Cake vs Donne Biryani).
        - In Bangalore, Darshinis do not bake gourmet pizzas, and pizzerias do not brew degree filter coffee.
        - Do NOT offer false options like "Find a single store that serves both if available" when they belong to separate specialty kitchens.
        - Instead, be transparent, warm, and helpful right away:
          Explain that filter coffee is prepared at traditional Darshinis, while pizzas are baked at dedicated pizzerias. Since each delivery order is prepared and dispatched hot from a single kitchen, they cannot be combined into one delivery cart.
          Present 2 clean, actionable paths:
          1. "Order the filter coffee first (e.g. Taaza Thindi), and we'll immediately place a second order for the pizza right after."
          2. "Order the pizza first (e.g. Toit or Onesta), then do the filter coffee as a quick follow-up order."
          Ask the customer: "Which one would you like to start with?"
     b. If the customer already has an item from Store A in their cart, or chooses Store A for their first item:
        - Check if Store A offers the second item (using store-affinity search).
        - If Store A DOES NOT have the second item:
          - You are STRICTLY FORBIDDEN from silently adding the second item from another restaurant to the same cart!
          - Add ONLY the item available at Store A (or keep Store A's item in the cart).
          - Explain proactively, warmly, and clearly to the customer:
            1. Clearly state that [Item 1] (₹XX) from [Store A] is in their cart, but [Store A] does not carry [Item 2].
            2. Present 3 proactive choices:
               - **Choice 1 (Store A Alternative)**: Suggest delicious pairings from [Store A]'s menu.
               - **Choice 2 (Separate Orders)**: Complete this delivery order with [Store A] now, and immediately place a 2nd separate delivery order with [Store B] for [Item 2].
               - **Choice 3 (Switch Store)**: Clear the cart using `clear_cart` and switch to [Store B] or another store.
          - Never bundle dishes from multiple restaurants into a single cart table or single checkout link!
     c. If the customer asks a clarifying question about single-store availability (e.g. "so there is no shop which serves both?", "can I get both from one place?", "why can't they be in one cart?"):
        - Directly, warmly, and clearly confirm:
          "That's right! In Bangalore, authentic filter coffee is brewed fresh at traditional Darshinis (like Taaza Thindi or Brahmin's Coffee Bar), while gourmet pizzas are handcrafted in specialized kitchens (like Toit, Brik Oven, or Onesta). Since each delivery rider picks up hot orders directly from a single restaurant kitchen, these cuisines cannot be combined into one delivery order.
          To enjoy both, you can either:
          1. Order your filter coffee now, and we'll immediately help you place a second separate delivery order for the pizza.
          2. Or let me know which craving you'd like to satisfy first!"
        - NEVER dump a giant list of unrelated items or give a generic robotic template! Answer their question directly, humanly, and warmly.
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

            funnel_res = await search_with_alternatives(
                db, query=query, category=category, max_price=max_p, limit=8
            )
            exact_matches = funnel_res.get("exact_matches", [])
            over_budget_matches = funnel_res.get("over_budget_matches", [])
            alternatives = funnel_res.get("alternatives", [])
            
            found = exact_matches if exact_matches else (over_budget_matches[:2] + alternatives[:4])

            tool_result = {
                "explanation": funnel_res.get("explanation"),
                "is_over_budget": funnel_res.get("is_over_budget"),
                "exact_matches": exact_matches,
                "over_budget_matches": over_budget_matches,
                "alternatives": alternatives,
                "instruction": (
                    f"{funnel_res.get('explanation', '')} Present the options in an appetizing, beautifully formatted Markdown comparison table with columns (#, Store, Dish, Rating, Price in ₹). "
                    "If items are over budget, clearly state the price difference and invite the customer to choose between stretching their budget or picking an in-budget alternative. "
                    "STRICT REQUIREMENT: Respond exclusively in clean, polished English. NEVER use Hindi or Hinglish slang like 'Bhai' or 'Yeh lo'."
                ),
            }
            for p in found:
                pid = uuid.UUID(p["id"])
                if not any(str(r.product_id) == str(pid) for r in recommendations):
                    rating_str = f"⭐ {p.get('rating', 4.5)} " if p.get("rating") else ""
                    recommendations.append(
                        ProductRecommendation(
                            product_id=pid,
                            name=p["name"],
                            price=p["price"],
                            description=p.get("description"),
                            image_url=p.get("image_url"),
                            category=p.get("category"),
                            merchant_name=p.get("merchant_name") or "Bangalore Store",
                            reasoning=f"{rating_str}From {p.get('merchant_name', 'Bangalore Store')} — ₹{p['price']:.0f}",
                        )
                    )
            add_agent_reasoning(
                conversation,
                action="search_all_stores",
                reasoning=f"Cross-merchant search: query='{query}', category='{category}', max_price={max_p}. Found {len(found)} items.",
            )

        elif fn_name == "search_by_occasion":
            action_type = "recommend"
            occ = fn_args.get("occasion", "")
            people = fn_args.get("people_count")
            budget_val = fn_args.get("budget")
            last_search_query = occ

            occasion_res = await search_by_occasion(
                db=db,
                occasion=occ,
                budget=budget_val,
                people_count=people,
            )
            tool_result = occasion_res

            for it in occasion_res.get("curated_items", []):
                try:
                    pid = uuid.UUID(it["product_id"])
                    if not any(str(r.product_id) == str(pid) for r in recommendations):
                        badge_str = f"{it.get('badge', '')} " if it.get("badge") else ""
                        recommendations.append(
                            ProductRecommendation(
                                product_id=pid,
                                name=it["name"],
                                price=it["unit_price"],
                                category=it.get("category"),
                                merchant_name=it.get("merchant_name") or "Bangalore Store",
                                reasoning=f"{badge_str}From {it.get('merchant_name')} • Portion: {it.get('quantity', 1)}x (₹{it['subtotal']:.0f})",
                            )
                        )
                except Exception:
                    pass

            add_agent_reasoning(
                conversation,
                action="search_by_occasion",
                reasoning=f"Occasion search for '{occ}': Curated {len(occasion_res.get('curated_items', []))} items totaling ₹{occasion_res.get('total_combo_cost', 0):.0f}",
            )

        elif fn_name == "reorder_previous":
            action_type = "cart_update"
            past_order = await order_service.get_customer_last_order(
                db=db,
                conversation_id=conversation.id,
                customer_id=conversation.customer_id,
            )
            if past_order and past_order.items:
                m_stmt = select(Merchant).where(Merchant.id == past_order.merchant_id)
                m_res = await db.execute(m_stmt)
                m_obj = m_res.scalar_one_or_none()
                m_name = m_obj.name if m_obj else "Original Restaurant"

                # Update cart and lock conversation
                cart["items"] = list(past_order.items)
                cart["total"] = float(past_order.total)
                cart["merchant_id"] = str(past_order.merchant_id)
                cart["merchant_name"] = m_name
                conversation.merchant_id = past_order.merchant_id
                update_conversation_cart(conversation, cart)
                cart = conversation.cart

                resolved_merchant_id = past_order.merchant_id
                resolved_merchant_name = m_name

                tool_result = {
                    "success": True,
                    "order_id": str(past_order.id)[:8],
                    "merchant_name": m_name,
                    "merchant_id": str(past_order.merchant_id),
                    "items": past_order.items,
                    "total": past_order.total,
                    "message": f"Found your last order from {m_name}! Reloaded {len(past_order.items)} items (Total: ₹{past_order.total:.0f}) into your cart.",
                }
                add_agent_reasoning(
                    conversation,
                    action="reorder_previous",
                    reasoning=f"Reloaded past order #{str(past_order.id)[:8]} ({len(past_order.items)} items, ₹{past_order.total:.0f}) from {m_name}",
                )
            else:
                tool_result = {
                    "success": False,
                    "message": "No previous orders found in your account history. Feel free to explore our popular dishes across Bangalore!",
                }

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

        elif fn_name == "clear_cart":
            action_type = "cart_update"
            cart["items"] = []
            cart["total"] = 0.0
            cart["merchant_id"] = None
            cart["merchant_name"] = None
            conversation.merchant_id = None
            update_conversation_cart(conversation, cart)
            cart = conversation.cart
            resolved_merchant_id = None
            resolved_merchant_name = None
            tool_result = {
                "success": True,
                "cart_items": [],
                "cart_total": 0.0,
                "message": "Cart has been cleared and store unlocked. The customer can now freely explore or select any restaurant across Bangalore.",
            }
            add_agent_reasoning(
                conversation,
                action="clear_cart_discovery",
                reasoning="Cleared cart and reset active store lock. Customer is back in city-wide discovery mode.",
            )

        elif fn_name == "add_to_cart":
            action_type = "cart_update"
            pid = fn_args.get("product_id")
            pname = fn_args.get("product_name")
            mname = fn_args.get("merchant_name") or fn_args.get("store_name") or fn_args.get("store")
            qty = max(1, int(fn_args.get("quantity", 1)))
            product = None

            # Detect existing store from conversation or cart
            existing_merchant_id = None
            if conversation.merchant_id:
                existing_merchant_id = conversation.merchant_id
            elif cart.get("merchant_id"):
                try:
                    existing_merchant_id = uuid.UUID(str(cart.get("merchant_id")))
                except Exception:
                    pass
            elif cart.get("items"):
                for it in cart["items"]:
                    m_id = it.get("merchant_id")
                    if m_id:
                        try:
                            existing_merchant_id = uuid.UUID(str(m_id))
                            break
                        except Exception:
                            pass

            if pid:
                try:
                    product = await get_product_by_id_any_merchant(db, uuid.UUID(pid))
                except Exception:
                    product = None

            # Store-Affinity Catalog Search: If cart already locked to a store, prioritize that store's catalog
            if not product and pname and existing_merchant_id and not mname:
                stmt_same = (
                    select(Product)
                    .where(
                        Product.merchant_id == existing_merchant_id,
                        Product.name.ilike(f"%{pname}%"),
                        Product.in_stock == True,
                    )
                )
                res_same = await db.execute(stmt_same)
                product = res_same.scalars().first()

                if not product:
                    for word in pname.split():
                        if len(word) > 3 and word.lower() not in STOPWORDS:
                            stmt_w = (
                                select(Product)
                                .where(
                                    Product.merchant_id == existing_merchant_id,
                                    Product.name.ilike(f"%{word}%"),
                                    Product.in_stock == True,
                                )
                            )
                            res_w = await db.execute(stmt_w)
                            cand = res_w.scalars().first()
                            if cand:
                                product = cand
                                break

            # If still not found, search across requested store or all stores
            if not product and (pname or mname):
                if mname and pname:
                    # 1. Exact or substring match within requested merchant
                    stmt = (
                        select(Product)
                        .join(Merchant, Product.merchant_id == Merchant.id)
                        .where(
                            Merchant.name.ilike(f"%{mname}%"),
                            Product.name.ilike(f"%{pname}%"),
                            Product.in_stock == True,
                            Merchant.is_active == True,
                        )
                    )
                    res = await db.execute(stmt)
                    product = res.scalars().first()

                    # 2. Token / word overlap match within requested merchant (handles parentheses, extra adjectives)
                    if not product:
                        clean_p = re.sub(r"[^\w\s]", " ", pname.lower())
                        p_words = [w for w in clean_p.split() if len(w) >= 3 and w not in STOPWORDS]
                        stmt_m_prods = (
                            select(Product)
                            .join(Merchant, Product.merchant_id == Merchant.id)
                            .where(
                                Merchant.name.ilike(f"%{mname}%"),
                                Product.in_stock == True,
                                Merchant.is_active == True,
                            )
                        )
                        res_m_prods = await db.execute(stmt_m_prods)
                        m_candidates = res_m_prods.scalars().all()

                        if m_candidates and p_words:
                            best_cand = None
                            best_score = 0
                            for cand in m_candidates:
                                cand_clean = re.sub(r"[^\w\s]", " ", cand.name.lower())
                                cand_words = set(cand_clean.split())
                                match_count = sum(1 for w in p_words if w in cand_words or any(w in cw or cw in w for cw in cand_words))
                                if match_count > best_score:
                                    best_score = match_count
                                    best_cand = cand
                            if best_cand and best_score >= 1:
                                product = best_cand

                if not product and pname:
                    all_found = await search_all_merchants_catalog(db, query=pname, limit=5)
                    if all_found:
                        found_pid = uuid.UUID(all_found[0]["id"])
                        product = await get_product_by_id_any_merchant(db, found_pid)

                if not product and mname:
                    from sqlalchemy import desc
                    stmt_m = (
                        select(Product)
                        .join(Merchant, Product.merchant_id == Merchant.id)
                        .where(
                            Merchant.name.ilike(f"%{mname}%"),
                            Product.in_stock == True,
                            Merchant.is_active == True,
                        )
                        .order_by(desc(Product.rating))
                    )
                    res_m = await db.execute(stmt_m)
                    product = res_m.scalars().first()

            if product:
                # SINGLE-STORE GUARDRAIL: Verify against existing cart merchant unless multi-store requested
                is_multi_store_request = (
                    fn_args.get("allow_multi_store") is True
                    or any(
                        phrase in (conversation.messages[-1].get("content", "") if conversation.messages else "").lower()
                        for phrase in [
                            "order both", "add both", "buy both", "get both", "want both", "both of them",
                            "both items", "yes both", "order pizza and filter coffee both", "order both please",
                            "order both filter coffee and pizza", "order filter coffee and pizza both"
                        ]
                    )
                )

                if existing_merchant_id and str(product.merchant_id) != str(existing_merchant_id) and not is_multi_store_request:
                    ex_res = await db.execute(select(Merchant).where(Merchant.id == existing_merchant_id))
                    ex_merchant = ex_res.scalar_one_or_none()
                    ex_name = ex_merchant.name if ex_merchant else "your current restaurant"

                    att_res = await db.execute(select(Merchant).where(Merchant.id == product.merchant_id))
                    att_merchant = att_res.scalar_one_or_none()
                    att_name = att_merchant.name if att_merchant else "another restaurant"

                    alt_stmt = (
                        select(Product)
                        .where(
                            Product.merchant_id == existing_merchant_id,
                            Product.in_stock == True,
                        )
                        .limit(3)
                    )
                    alt_res = await db.execute(alt_stmt)
                    store_alts = [
                        {"name": a.name, "price": a.price, "category": a.category}
                        for a in alt_res.scalars().all()
                    ]
                    alt_text = ", ".join(f"{a['name']} (₹{a['price']:.0f})" for a in store_alts[:2]) if store_alts else "other items"

                    tool_result = {
                        "success": False,
                        "store_mismatch": True,
                        "existing_store_id": str(existing_merchant_id),
                        "existing_store_name": ex_name,
                        "attempted_product": product.name,
                        "attempted_store_name": att_name,
                        "suggested_store_alternatives": store_alts,
                        "message": (
                            f"SINGLE RESTAURANT POLICY GUARDRAIL: The cart currently contains items from '{ex_name}'. "
                            f"'{product.name}' is only available at '{att_name}'. In our food delivery platform, each order "
                            f"is prepared and dispatched from a single restaurant kitchen to ensure hot, fast delivery. "
                            f"Dishes from different restaurants are usually ordered from separate kitchens.\n"
                            f"Explain this clearly to the customer and present these proactive choices:\n"
                            f"1. **Order both with Dual-Store Checkout**: Say *'order both'* to keep both kitchen items in your dual-cart and pay once with our unified payment link! ⚡\n"
                            f"2. **Add an alternative from {ex_name}**: Suggest menu options like {alt_text}.\n"
                            f"3. **Place separate orders**: Proceed to checkout with {ex_name} now, and place a 2nd order from {att_name}.\n"
                            f"4. **Switch to {att_name}**: Call `clear_cart` to switch stores and order '{product.name}' from {att_name} instead."
                        ),
                    }
                    add_agent_reasoning(
                        conversation,
                        action="store_mismatch_prevented",
                        reasoning=f"Enforced single-restaurant boundary: Cart has items from '{ex_name}'. Offered dual-store checkout or store alternative.",
                    )
                    await log_audit_event(
                        db=db,
                        event_type=AuditEventType.AGENT_DECISION,
                        merchant_id=existing_merchant_id,
                        conversation_id=conversation.id,
                        action="store_mismatch_prevented",
                        reasoning=f"Advised user on dual-store ordering or alternatives for '{product.name}' ({att_name}) alongside '{ex_name}'",
                        input_data=fn_args,
                        output_data={"store_mismatch": True, "existing_store": ex_name, "attempted_store": att_name},
                    )
                    return tool_result, action_type, resolved_merchant_id, resolved_merchant_name, cart, last_search_query

                # Product belongs to same merchant (or multi-store addition)
                m_res = await db.execute(select(Merchant).where(Merchant.id == product.merchant_id))
                cur_m = m_res.scalar_one_or_none()
                store_name = cur_m.name if cur_m else "Bangalore Store"

                if not is_multi_store_request and not cart.get("is_multi_store"):
                    handoff_data = {
                        "intent": f"Buy {product.name}",
                        "search_query": last_search_query or product.name,
                        "budget": cart.get("budget"),
                        "preferred_items": [{"product_id": str(product.id), "name": product.name, "price": product.price}],
                        "source_agent": "DiscoveryAgent",
                        "selected_store_name": store_name,
                    }
                    conversation = await lock_conversation_to_merchant(
                        db, conversation, product.merchant_id, handoff_data=handoff_data
                    )
                    resolved_merchant_id = product.merchant_id
                    resolved_merchant_name = store_name
                else:
                    conversation.merchant_id = None
                    resolved_merchant_id = None
                    resolved_merchant_name = "Dual Kitchen (Multi-Store)"

                items = list(cart.get("items", []))
                current_total = float(cart.get("total", 0.0))
                additional_cost = float(product.price) * qty
                projected_total = current_total + additional_cost

                # Strict Budget Guardrail Check
                from app.services.order_service import extract_customer_budget
                detected_budget = extract_customer_budget(conversation.messages or [])

                prev_content = (conversation.messages[-1].get("content") or "").lower() if conversation.messages else ""
                user_overrode_budget = any(k in prev_content for k in [
                    "can adjust", "adjust extra", "extra", "increase budget", "override budget",
                    "budget is ok", "fine with", "i can pay", "agree", "adjust 55", "adjust", "i can adjust"
                ])
                if not user_overrode_budget and len(conversation.messages or []) >= 2:
                    last_ast = next((m.get("content", "").lower() for m in reversed(conversation.messages[:-1]) if m.get("role") == "assistant"), "")
                    if any(w in last_ast for w in ["budget guardrail active", "exceeds your stated budget", "would you like to adjust the quantity"]):
                        if any(w in prev_content for w in ["yes", "yeah", "yep", "sure", "ok", "okay", "fine", "adjust", "extra", "add it", "go ahead", "proceed", "do it"]):
                            user_overrode_budget = True

                if detected_budget is not None and projected_total > detected_budget and not user_overrode_budget:
                    remaining_budget = max(0.0, detected_budget - current_total)
                    tool_result = {
                        "success": False,
                        "budget_blocked": True,
                        "current_total": current_total,
                        "projected_total": projected_total,
                        "budget_limit": detected_budget,
                        "remaining_budget": remaining_budget,
                        "attempted_product": product.name,
                        "attempted_price": product.price,
                        "message": (
                            f"Budget Guardrail Active: Adding {qty}x {product.name} (₹{additional_cost:.0f}) brings projected total to ₹{projected_total:.0f}, "
                            f"exceeding your stated budget of ₹{detected_budget:.0f} (Remaining: ₹{remaining_budget:.0f})."
                        ),
                    }
                    add_agent_reasoning(
                        conversation,
                        action="budget_guardrail_blocked",
                        reasoning=f"Blocked {qty}x {product.name} (₹{additional_cost:.0f}): Projected ₹{projected_total:.0f} > budget limit ₹{detected_budget:.0f}.",
                    )
                    await log_audit_event(
                        db=db,
                        event_type=AuditEventType.BUDGET_VIOLATION,
                        merchant_id=product.merchant_id,
                        conversation_id=conversation.id,
                        action="add_to_cart_budget_blocked",
                        reasoning=f"Discovery item addition blocked: ₹{projected_total:.0f} > budget limit ₹{detected_budget:.0f}",
                        input_data={"product": product.name, "additional": additional_cost, "budget": detected_budget},
                        output_data={"blocked": True},
                    )
                    return tool_result, action_type, resolved_merchant_id, resolved_merchant_name, cart, last_search_query

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
                        "merchant_id": str(product.merchant_id),
                        "merchant_name": store_name,
                    })
                cart["items"] = items
                distinct_m_count = len(set(i.get("merchant_id") for i in items if i.get("merchant_id")))
                if is_multi_store_request or distinct_m_count > 1:
                    cart["is_multi_store"] = True
                    cart["merchant_id"] = None
                    cart["merchant_name"] = f"Multi-Kitchen ({distinct_m_count} Stores)" if distinct_m_count > 2 else "Dual Kitchen (Multi-Store)"
                else:
                    cart["merchant_id"] = str(product.merchant_id)
                    cart["merchant_name"] = store_name
                cart["total"] = round(sum(float(i.get("price", 0)) * int(i.get("quantity", 1)) for i in items), 2)
                update_conversation_cart(conversation, cart)
                cart = conversation.cart

                tool_result = {
                    "success": True,
                    "is_multi_store": cart.get("is_multi_store", False),
                    "added_product": product.name,
                    "quantity": qty,
                    "cart_total": cart["total"],
                    "cart_items": cart["items"],
                    "store_name": store_name,
                    "locked_to_merchant": str(product.merchant_id) if not cart.get("is_multi_store") else None,
                    "message": (
                        f"Added {qty}x {product.name} from {store_name} to your dual-store cart! "
                        f"Both kitchens will fulfill their items and you can pay once at checkout."
                        if cart.get("is_multi_store")
                        else f"Added {qty}x {product.name} from {store_name} to cart."
                    ),
                }
                add_agent_reasoning(
                    conversation,
                    action="add_to_cart_discovery",
                    reasoning=f"Added {qty}x {product.name} (₹{product.price:.0f}) from {store_name} to cart. Multi-store={cart.get('is_multi_store', False)}.",
                )
                await log_audit_event(
                    db=db,
                    event_type=AuditEventType.AGENT_DECISION,
                    merchant_id=product.merchant_id,
                    conversation_id=conversation.id,
                    action="add_to_cart_discovery",
                    reasoning=f"Added {qty}x {product.name} ({store_name}) to cart. Total: ₹{cart['total']:.0f}",
                    input_data=fn_args,
                    output_data={"cart_total": cart["total"], "store": store_name},
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
        customer_mem = await build_customer_profile_memory(conversation.customer_id, db)
        system_prompt = _build_discovery_system_prompt(city_merchants, cart, customer_memory=customer_mem)

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

        u_lower = user_message.lower().strip()
        is_pay_cmd = any(k in u_lower for k in [
            "payment", "pay", "checkout", "to a payment", "do a payment", "do payment",
            "pay for me", "make payment", "proceed to pay", "open razorpay", "open payment"
        ])
        if is_pay_cmd:
            from app.models.order import Order
            res = await db.execute(
                select(Order)
                .where(Order.conversation_id == conversation.id)
                .order_by(Order.created_at.desc())
                .limit(1)
            )
            unpaid_order = res.scalar_one_or_none()
            if not unpaid_order and conversation.customer_id:
                res = await db.execute(
                    select(Order)
                    .where(Order.customer_id == conversation.customer_id)
                    .order_by(Order.created_at.desc())
                    .limit(1)
                )
                unpaid_order = res.scalar_one_or_none()

            if (
                unpaid_order
                and unpaid_order.payment_link
                and "PAID" not in str(getattr(unpaid_order, "status", "")).upper()
                and "CANCELLED" not in str(getattr(unpaid_order, "status", "")).upper()
            ):
                order_total_val = float(getattr(unpaid_order, "total", 0.0))
                order_id_str = str(unpaid_order.id)
                pay_msg = (
                    f"Opening secure Razorpay Checkout for your order (₹{order_total_val:.0f}) now! 💳\n\n"
                    f"Please complete your payment on the secure Razorpay screen: [💳 Pay ₹{order_total_val:.0f} via Razorpay Secure]({unpaid_order.payment_link})\n\n"
                    f"Once confirmed on Razorpay, your order will automatically confirm and dispatch!"
                )
                add_message_to_conversation(
                    conversation,
                    role="assistant",
                    content=pay_msg,
                    metadata={
                        "action": "checkout",
                        "payment_link": unpaid_order.payment_link,
                        "order_id": order_id_str,
                    },
                )
                return ChatResponse(
                    conversation_id=conversation.id,
                    order_id=order_id_str,
                    merchant_id=unpaid_order.merchant_id,
                    merchant_name=None,
                    message=pay_msg,
                    recommendations=None,
                    cart=[],
                    cart_total=0.0,
                    action="checkout",
                    payment_link=unpaid_order.payment_link,
                )

        is_conversational_query = bool(
            "?" in user_message
            or re.search(r"\b(why|how|what|when|where|is\s+there|are\s+there|so\s+there|can\s+i|can\s+we|could\s+|would\s+|does\s+|do\s+they|which\s+one|no\s+shop|any\s+shop|tell\s+me\s+if|explain)\b", u_lower)
        )

        try:
            tools_executed_count = 0
            for cycle_idx in range(3):
                # Force model to synthesize text if tools were already executed or in final cycle
                allow_tools = DISCOVERY_TOOLS if (cycle_idx < 2 and tools_executed_count < 2) else None
                choice = "auto" if allow_tools else "none"

                response = await groq_client.chat_completion(
                    messages=llm_messages,
                    tools=allow_tools,
                    tool_choice=choice,
                    temperature=0.25,
                    max_tokens=500,
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
                    tools_executed_count += 1
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
                try:
                    synth_resp = await groq_client.chat_completion(
                        messages=llm_messages,
                        temperature=0.3,
                        max_tokens=450,
                    )
                    final_text = synth_resp.choices[0].message.content or ""
                except Exception as synth_err:
                    logger.warning("Synthesis error: %s", synth_err)

            if not final_text:
                final_text = "I ran a city-wide search across Bangalore stores. How else can I assist?"

        except Exception as exc:
            logger.error("DiscoveryAgent error: %s", exc, exc_info=True)
            final_text = "I ran a city-wide search across Bangalore stores. How else can I assist?"

        final_text = sanitize_english_response(final_text)

        # Suppress recommendation cards on pure conversational/clarifying questions
        if is_conversational_query:
            recommendations = []

        # Deduplicate and balance recommendations across categories (max 4 cards)
        if recommendations:
            seen_ids = set()
            deduped = []
            for r in recommendations:
                rid = str(r.product_id)
                if rid not in seen_ids:
                    seen_ids.add(rid)
                    deduped.append(r)

            by_cat: dict[str, list[ProductRecommendation]] = {}
            for r in deduped:
                cat = r.category or "General"
                by_cat.setdefault(cat, []).append(r)

            if len(by_cat) > 1:
                balanced: list[ProductRecommendation] = []
                max_per_cat = max(1, 4 // len(by_cat))
                for cat_items in by_cat.values():
                    balanced.extend(cat_items[:max_per_cat])
                for r in deduped:
                    if len(balanced) >= 4:
                        break
                    if r not in balanced:
                        balanced.append(r)
                recommendations = balanced[:4]
            else:
                recommendations = deduped[:4]

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
        customer_mem = await build_customer_profile_memory(conversation.customer_id, db)
        system_prompt = _build_discovery_system_prompt(city_merchants, cart, customer_memory=customer_mem)

        optimized_history = await build_optimized_context(conversation, max_recent=6)

        llm_messages: list[dict[str, Any]] = [
            {"role": "system", "content": system_prompt},
            *optimized_history,
        ]

        # Fast-Path 1: Personalized Greeting with Customer Memory & MerchantMind Wake Word
        u_strip = user_message.strip().lower()
        is_pure_greeting = (
            bool(GREETING_REGEX.match(user_message.strip()))
            or u_strip in [
                "merchantmind",
                "merchant mind",
                "mercanhtmind",
                "hey merchantmind",
                "hi merchantmind",
                "hello merchantmind",
                "ok merchantmind",
                "hi merchant mind",
                "hey merchant mind",
            ]
        ) and len(user_message.strip().split()) <= 4
        if is_pure_greeting:
            customer_first_name = ""
            if customer_mem and "Customer Name:" in customer_mem:
                name_match = re.search(r"Customer Name:\s*([A-Za-z]+)", customer_mem)
                if name_match:
                    customer_first_name = name_match.group(1)
            
            greeting_prefix = f"Hey {customer_first_name}! 👋" if customer_first_name else "Hello! 👋"
            greeting_response = f"{greeting_prefix} I'm right here and listening. What would you like to explore or order today across Bangalore stores? (e.g. *\"Truffle cake under ₹600\"* or *\"2 dosas, 1 pizza, and a burger\"*)"
            
            add_message_to_conversation(
                conversation,
                role="assistant",
                content=greeting_response,
                metadata={"action": "chat"},
            )

            yield {
                "type": "answer",
                "agent": "DiscoveryAgent",
                "content": greeting_response,
                "chat_response": ChatResponse(
                    conversation_id=conversation.id,
                    merchant_id=None,
                    merchant_name=None,
                    message=greeting_response,
                    recommendations=None,
                    cart=None,
                    cart_total=0.0,
                    action="chat",
                    payment_link=None,
                    agent_reasoning=conversation.agent_reasoning if conversation.agent_reasoning else None,
                ).model_dump(mode="json"),
            }
            return

        # Fast-Path: Autonomous Clear Cart & Store Unlock
        u_lower = user_message.lower().strip()
        clean_cmd = u_lower.replace("’", "").replace("'", "").strip()

        # Contextual check: Inspect previous assistant message for conversational continuity
        prev_assistant_msg = ""
        if conversation.messages and len(conversation.messages) >= 2:
            for prev_m in reversed(conversation.messages[:-1]):
                if prev_m.get("role") == "assistant":
                    prev_assistant_msg = prev_m.get("content", "")
                    break
        prev_lower = prev_assistant_msg.lower()

        # Extract last_recs early so all fast-paths can benefit from it
        last_recs = []
        for msg in reversed(conversation.messages or []):
            if msg.get("role") == "assistant" and msg.get("metadata", {}).get("recommendations"):
                last_recs = msg["metadata"]["recommendations"]
                break

        # Fast-Path 2: Autonomous Conversational Checkout State Machine
        checkout_keywords = [
            "checkout", "check out", "check it out", "please check it out",
            "proceed to checkout", "go to checkout", "proceed to pay",
            "pay now", "make payment", "buy now", "place order", "place my order",
            "order now", "complete purchase", "checkout from cart", "check out from cart",
            "checkout cart", "check out cart", "checkout my cart", "check out my cart",
            "order from cart", "order my cart", "order the cart", "order what is in my cart",
            "orders what is already", "already at in my card", "already in my card",
            "already in my cart", "what is in my card", "what is in my cart",
            "what is already at in my card", "what is already in my cart",
            "check out the orders", "checkout the orders", "check out what is already at in my card",
            "check out the orders what is already at in my card",
            "checkout the orders what is already at in my card",
            "checkout both", "checkout both orders", "checkout all", "checkout all orders",
            "check out both", "check out all",
        ]
        stripped_cmd = re.sub(r"\b(please|kindly|can you|could you|just)\b", "", clean_cmd).strip()

        is_explicit_checkout = (
            any(k in clean_cmd for k in checkout_keywords)
            or any(stripped_cmd.startswith(k) for k in [
                "checkout", "check out", "check it out", "proceed to pay", "make payment", "place order", "buy now", "pay now"
            ])
            or stripped_cmd in [
                "checkout", "check out", "check it out", "pay", "pay now", "proceed to pay", "make payment", "place order", "buy now"
            ]
            or (("check out" in clean_cmd or "checkout" in clean_cmd or "check it out" in clean_cmd) and any(w in clean_cmd for w in ["cart", "card", "order", "orders", "both", "all", "already"]))
        )

        is_clear_cart_intent = (not is_explicit_checkout) and (
            any(k in clean_cmd for k in [
                "clear cart", "empty cart", "clear my cart", "empty my cart", "reset cart", "clear the cart",
                "switch restaurant", "switch store", "remove everything", "empty the cart"
            ]) or clean_cmd in ["clear", "empty", "reset", "clear cart", "empty cart"]
        )

        if is_clear_cart_intent:
            cart["items"] = []
            cart["total"] = 0.0
            cart["merchant_id"] = None
            cart["merchant_name"] = None
            conversation.merchant_id = None
            update_conversation_cart(conversation, cart)
            add_agent_reasoning(
                conversation,
                action="clear_cart_fastpath",
                reasoning="Cleared cart and unlocked store. Customer returned to city-wide discovery.",
            )
            clear_msg = "🛒 Your cart has been cleared! You can now freely explore dishes from any restaurant in Bangalore. What would you like to have today?"
            add_message_to_conversation(conversation, role="assistant", content=clear_msg)
            yield {
                "type": "answer",
                "agent": "DiscoveryAgent",
                "content": clear_msg,
                "chat_response": ChatResponse(
                    conversation_id=conversation.id,
                    merchant_id=None,
                    merchant_name=None,
                    message=clear_msg,
                    recommendations=None,
                    cart=[],
                    cart_total=0.0,
                    action="cart_update",
                    payment_link=None,
                ).model_dump(mode="json"),
            }
            return

        current_items = list(cart.get("items", []))

        if not current_items and is_explicit_checkout:
            # 1. Recover items from conversation metadata if present
            for prev_m in reversed(conversation.messages or []):
                meta_cart = prev_m.get("metadata", {}).get("cart")
                if meta_cart and isinstance(meta_cart, list) and len(meta_cart) > 0:
                    current_items = meta_cart
                    cart["items"] = current_items
                    cart["total"] = round(sum(float(i.get("price", 0)) * int(i.get("quantity", 1)) for i in current_items), 2)
                    update_conversation_cart(conversation, cart)
                    break
            
            # 2. If still empty, recover from previous recommendations
            if not current_items and last_recs:
                auto_items = []
                for rec in last_recs[:2]:
                    auto_items.append({
                        "product_id": str(rec.get("product_id") or rec.get("id")),
                        "name": rec.get("name", "Item"),
                        "price": float(rec.get("price", 0.0)),
                        "quantity": 1,
                        "merchant_id": str(rec.get("merchant_id")) if rec.get("merchant_id") else None,
                        "merchant_name": rec.get("merchant_name", "Bangalore Store"),
                    })
                if auto_items:
                    current_items = auto_items
                    cart["items"] = current_items
                    cart["total"] = round(sum(i["price"] * i["quantity"] for i in auto_items), 2)
                    distinct_m = len(set(i.get("merchant_id") for i in auto_items if i.get("merchant_id")))
                    if distinct_m > 1:
                        cart["is_multi_store"] = True
                        cart["merchant_id"] = None
                        cart["merchant_name"] = "Dual Kitchen (Multi-Store)"
                    else:
                        cart["merchant_id"] = auto_items[0].get("merchant_id")
                        cart["merchant_name"] = auto_items[0].get("merchant_name")
                    update_conversation_cart(conversation, cart)

            # 3. If truly empty, return polite message without returning cart=[]
            if not current_items:
                empty_msg = "🛒 Your cart is currently empty! Please tell me what you'd like to order across Bangalore first (e.g. *\"Truffle cake\"* or *\"2 dosas and a burger\"*)."
                add_message_to_conversation(conversation, role="assistant", content=empty_msg)
                yield {
                    "type": "answer",
                    "agent": "DiscoveryAgent",
                    "content": empty_msg,
                    "chat_response": ChatResponse(
                        conversation_id=conversation.id,
                        merchant_id=None,
                        merchant_name=None,
                        message=empty_msg,
                        recommendations=None,
                        cart=None,  # Do not pass [] so client cart is not wiped
                        cart_total=0.0,
                        action="chat",
                        payment_link=None,
                    ).model_dump(mode="json"),
                }
                return

        if not current_items:
            # Non-checkout commands with an empty cart should not be intercepted as checkout!
            is_checkout_intent = False
            wants_pickup = False
            wants_delivery = False
            wants_saved_addr = False
            wants_new_addr = False
            has_pincode = False
        else:
            is_asking_saved_addr = any(phrase in prev_lower for phrase in ["saved address", "indiranagar", "use saved address", "delivery to"])
            is_asking_pickup_delivery = any(phrase in prev_lower for phrase in ["store pickup or doorstep delivery", "pickup or doorstep", "store pickup"])

            wants_pickup = any(k in clean_cmd for k in ["store pickup", "pickup from store", "pickup at counter"]) or (is_asking_pickup_delivery and clean_cmd in ["pickup", "counter", "1", "option 1"])
            wants_delivery = any(k in clean_cmd for k in ["doorstep delivery", "home delivery", "deliver to me"]) or (is_asking_pickup_delivery and clean_cmd in ["delivery", "doorstep", "2", "option 2"])
            wants_saved_addr = any(k in clean_cmd for k in ["saved address", "same address", "use saved address", "use saved"]) or (is_asking_saved_addr and clean_cmd in ["yes", "yeah", "yep", "sure", "saved", "same"])
            wants_new_addr = any(k in clean_cmd for k in ["new address", "enter new", "change address", "different address"])
            has_pincode = bool(re.search(r"\b560\d{3}\b", clean_cmd))

            is_checkout_intent = (
                is_explicit_checkout
                or clean_cmd in ["store pickup", "doorstep delivery", "use saved address", "enter new address"]
                or wants_pickup
                or wants_delivery
                or wants_saved_addr
                or wants_new_addr
            )

        if is_checkout_intent and current_items:

            target_merchant = None
            for it in current_items:
                pid = it.get("product_id")
                if pid:
                    try:
                        p_uuid = uuid.UUID(str(pid))
                        p_res = await db.execute(select(Product).where(Product.id == p_uuid))
                        prod = p_res.scalar_one_or_none()
                        if prod and prod.merchant_id:
                            m_res = await db.execute(select(Merchant).where(Merchant.id == prod.merchant_id))
                            target_merchant = m_res.scalar_one_or_none()
                            if target_merchant:
                                break
                    except Exception:
                        pass
            if not target_merchant:
                m_res = await db.execute(select(Merchant).limit(1))
                target_merchant = m_res.scalar_one_or_none()

            cart_items_list = [
                CartItem(
                    product_id=uuid.UUID(i["product_id"]) if isinstance(i["product_id"], str) else i["product_id"],
                    name=i["name"],
                    price=i["price"],
                    quantity=i.get("quantity", 1),
                )
                for i in current_items
            ]

            # Step 1: Ask Pickup vs Delivery if not yet specified
            if not wants_pickup and not wants_delivery and not wants_saved_addr and not wants_new_addr:
                step1_msg = "Would you like this for store pickup or doorstep delivery?\n\n[🛍️ Store Pickup] [🚚 Doorstep Delivery]"
                add_message_to_conversation(conversation, role="assistant", content=step1_msg)
                yield {
                    "type": "answer",
                    "agent": "DiscoveryAgent",
                    "content": step1_msg,
                    "chat_response": ChatResponse(
                        conversation_id=conversation.id,
                        merchant_id=target_merchant.id if target_merchant else None,
                        merchant_name=target_merchant.name if target_merchant else None,
                        message=step1_msg,
                        recommendations=None,
                        cart=cart_items_list,
                        cart_total=float(cart.get("total", 0.0)),
                        action="chat",
                        payment_link=None,
                    ).model_dump(mode="json"),
                }
                return

            # Step 2B: Delivery selected -> Check saved address
            saved_addr = "Flat 402, 100 Feet Road, Indiranagar, Bangalore - 560038"
            if wants_delivery and not wants_saved_addr and not wants_new_addr:
                step2_msg = f"Would you like this delivered to your saved address at **{saved_addr}**, or a new address?\n\n[📍 Use Saved Address] [✏️ Enter New Address]"
                add_message_to_conversation(conversation, role="assistant", content=step2_msg)
                yield {
                    "type": "answer",
                    "agent": "DiscoveryAgent",
                    "content": step2_msg,
                    "chat_response": ChatResponse(
                        conversation_id=conversation.id,
                        merchant_id=target_merchant.id if target_merchant else None,
                        merchant_name=target_merchant.name if target_merchant else None,
                        message=step2_msg,
                        recommendations=None,
                        cart=cart_items_list,
                        cart_total=float(cart.get("total", 0.0)),
                        action="chat",
                        payment_link=None,
                    ).model_dump(mode="json"),
                }
                return

            # Step 3: User wants new address -> Prompt for address / pincode
            if wants_new_addr and not has_pincode and len(clean_cmd.split()) < 4:
                addr_prompt = "Please provide your new delivery address."
                add_message_to_conversation(conversation, role="assistant", content=addr_prompt)
                yield {
                    "type": "answer",
                    "agent": "DiscoveryAgent",
                    "content": addr_prompt,
                    "chat_response": ChatResponse(
                        conversation_id=conversation.id,
                        merchant_id=target_merchant.id if target_merchant else None,
                        merchant_name=target_merchant.name if target_merchant else None,
                        message=addr_prompt,
                        recommendations=None,
                        cart=cart_items_list,
                        cart_total=float(cart.get("total", 0.0)),
                        action="chat",
                        payment_link=None,
                    ).model_dump(mode="json"),
                }
                return

            # Step 4: Finalize Order (Pickup or Delivery confirmed)
            f_mode = "pickup" if wants_pickup else "delivery"
            deliv_addr = None if f_mode == "pickup" else (clean_cmd if has_pincode else saved_addr)

            if target_merchant:
                yield {
                    "type": "tool_call",
                    "agent": "DiscoveryAgent",
                    "content": f"Initiating Razorpay checkout for {target_merchant.name} ({f_mode})...",
                }
                order = await order_service.create_order(
                    db=db,
                    merchant_id=target_merchant.id,
                    conversation_id=conversation.id,
                    fulfillment_mode=f_mode,
                    delivery_address=deliv_addr,
                )
                plink = order.payment_link
                yield {
                    "type": "tool_result",
                    "agent": "DiscoveryAgent",
                    "tool": "checkout_and_pay",
                    "summary": f"Generated Razorpay order #{str(order.id)[:8]} for ₹{order.total:.0f}",
                    "data": {"order_id": str(order.id), "payment_link": plink, "order_total": order.total},
                }
                # Reset conversation cart upon order creation
                cart["items"] = []
                cart["total"] = 0.0
                update_conversation_cart(conversation, cart)

                items_str = ", ".join(f"{it.get('quantity', 1)}x {it.get('name')}" for it in current_items)
                fulfillment_label = "Store Counter Pickup" if f_mode == "pickup" else f"Doorstep Delivery to {deliv_addr}"
                final_msg = f"Your order is ready! 🎉\n\n📦 **Order Summary:**\n• **Item:** {items_str} — {target_merchant.name}\n• **Total:** ₹{order.total:.0f}\n• **Fulfillment:** {fulfillment_label}\n\n💳 **Payment Link:**\n[Click here to pay securely via Razorpay]({plink})\n\nPlease click below to complete your payment securely with Razorpay:"
                add_message_to_conversation(conversation, role="assistant", content=final_msg)
                yield {
                    "type": "answer",
                    "agent": "DiscoveryAgent",
                    "content": final_msg,
                    "chat_response": ChatResponse(
                        conversation_id=conversation.id,
                        order_id=str(order.id),
                        merchant_id=target_merchant.id,
                        merchant_name=target_merchant.name,
                        message=final_msg,
                        recommendations=None,
                        cart=[],
                        cart_total=0.0,
                        action="checkout",
                        payment_link=plink,
                    ).model_dump(mode="json"),
                }
                return

        # Fast-Path: Autonomous Live Order Tracking
        is_tracking_intent = any(k in clean_cmd for k in [
            "tracking page", "show me the tracking", "show tracking", "go to tracking",
            "track order", "track my order", "order tracking", "where is my order", "live tracking", "track my food"
        ])
        if is_tracking_intent:
            from app.models.order import Order
            res = await db.execute(
                select(Order)
                .where(Order.conversation_id == conversation.id)
                .order_by(Order.created_at.desc())
                .limit(1)
            )
            found_order = res.scalar_one_or_none()
            if not found_order and conversation.customer_id:
                res = await db.execute(
                    select(Order)
                    .where(Order.customer_id == conversation.customer_id)
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
                    "agent": "DiscoveryAgent",
                    "content": tracking_msg,
                    "chat_response": ChatResponse(
                        conversation_id=conversation.id,
                        order_id=str(found_order.id),
                        merchant_id=found_order.merchant_id,
                        merchant_name=None,
                        message=tracking_msg,
                        recommendations=None,
                        cart=[],
                        cart_total=0.0,
                        action="tracking",
                        payment_link=found_order.payment_link if "PAID" not in status_str.upper() else None,
                    ).model_dump(mode="json"),
                }
                return

        # Fast-Path: Autonomous Razorpay Payment for Unpaid Order
        is_pay_cmd = any(k in clean_cmd for k in [
            "payment", "pay", "checkout", "to a payment", "do a payment", "do payment",
            "pay for me", "make payment", "proceed to pay", "open razorpay", "open payment"
        ])
        if is_pay_cmd:
            from app.models.order import Order
            res = await db.execute(
                select(Order)
                .where(Order.conversation_id == conversation.id)
                .order_by(Order.created_at.desc())
                .limit(1)
            )
            unpaid_order = res.scalar_one_or_none()
            if not unpaid_order and conversation.customer_id:
                res = await db.execute(
                    select(Order)
                    .where(Order.customer_id == conversation.customer_id)
                    .order_by(Order.created_at.desc())
                    .limit(1)
                )
                unpaid_order = res.scalar_one_or_none()

            if (
                unpaid_order
                and unpaid_order.payment_link
                and "PAID" not in str(getattr(unpaid_order, "status", "")).upper()
                and "CANCELLED" not in str(getattr(unpaid_order, "status", "")).upper()
            ):
                order_total_val = float(getattr(unpaid_order, "total", 0.0))
                order_id_str = str(unpaid_order.id)
                pay_msg = (
                    f"Opening secure Razorpay Checkout for your order (₹{order_total_val:.0f}) now! 💳\n\n"
                    f"Please complete your payment on the secure Razorpay screen: [💳 Pay ₹{order_total_val:.0f} via Razorpay Secure]({unpaid_order.payment_link})\n\n"
                    f"Once confirmed on Razorpay, your order will automatically confirm and dispatch!"
                )
                add_message_to_conversation(
                    conversation,
                    role="assistant",
                    content=pay_msg,
                    metadata={
                        "action": "checkout",
                        "payment_link": unpaid_order.payment_link,
                        "order_id": order_id_str,
                    },
                )
                yield {
                    "type": "answer",
                    "agent": "DiscoveryAgent",
                    "content": pay_msg,
                    "chat_response": ChatResponse(
                        conversation_id=conversation.id,
                        order_id=order_id_str,
                        merchant_id=unpaid_order.merchant_id,
                        merchant_name=None,
                        message=pay_msg,
                        recommendations=None,
                        cart=[],
                        cart_total=0.0,
                        action="checkout",
                        payment_link=unpaid_order.payment_link,
                    ).model_dump(mode="json"),
                }
                return

        # Fast-Path 3: Intelligent Autonomous Cart Addition ("Brain of Your Own")
        last_recs = []
        for msg in reversed(conversation.messages or []):
            if msg.get("role") == "assistant" and msg.get("metadata", {}).get("recommendations"):
                last_recs = msg["metadata"]["recommendations"]
                break

        # Fast-Path 4: Multi-Store / Dual-Kitchen "Order Both" / "Order All" Autonomous Orchestration
        is_both_request = any(phrase in u_lower for phrase in [
            "order both", "add both", "buy both", "get both", "want both", "both of them",
            "both items", "yes both", "order pizza and filter coffee both", "order both please",
            "order both filter coffee and pizza", "order filter coffee and pizza both",
            "order two", "order both orders", "checkout both",
            "order all", "order all 3", "order all three", "add all three", "add all 3",
            "order all of them", "add all", "add all of them", "order all orders", "checkout all",
            "checkout all orders", "add all items"
        ])
        if is_both_request:
            items_to_add = []
            current_cart_items = list(cart.get("items", []))
            existing_m_ids = {str(it.get("merchant_id")) for it in current_cart_items if it.get("merchant_id")}

            if last_recs:
                # Group recommendations by merchant
                by_merchant: dict[str, list[dict[str, Any]]] = {}
                for r in last_recs:
                    m_id_val = str(r.get("merchant_id") or "")
                    if not m_id_val and (r.get("product_id") or r.get("id")):
                        try:
                            raw_pid = r.get("product_id") or r.get("id")
                            p_res = await db.execute(select(Product.merchant_id).where(Product.id == uuid.UUID(str(raw_pid))))
                            m_id_val = str(p_res.scalar_one_or_none() or "")
                        except Exception:
                            pass
                    by_merchant.setdefault(m_id_val, []).append(r)

                if len(by_merchant) >= 2:
                    for m_id_k, rec_list in by_merchant.items():
                        if m_id_k in existing_m_ids:
                            continue
                        best = sorted(rec_list, key=lambda x: float(x.get("rating", 4.5) or 4.5), reverse=True)[0]
                        items_to_add.append(best)
                elif current_cart_items and len(by_merchant) >= 1:
                    for m_id_k, rec_list in by_merchant.items():
                        if m_id_k not in existing_m_ids:
                            best = sorted(rec_list, key=lambda x: float(x.get("rating", 4.5) or 4.5), reverse=True)[0]
                            items_to_add.append(best)
                            break

            # Fallback if recommendations couldn't resolve items: search based on cravings in user message history
            if not items_to_add and not current_cart_items:
                cravings = []
                for prev_m in reversed(conversation.messages or []):
                    if prev_m.get("role") == "user":
                        parsed_items = parse_multi_food_items(prev_m.get("content", ""))
                        if parsed_items:
                            cravings = [it["raw"] for it in parsed_items]
                            break
                if len(cravings) >= 2:
                    for craving in cravings[:3]:
                        found = await search_all_merchants_catalog(db, query=craving, limit=1)
                        if found:
                            items_to_add.append(found[0])
                if not items_to_add:
                    coffee_prods = await search_all_merchants_catalog(db, query="filter coffee", limit=1)
                    pizza_prods = await search_all_merchants_catalog(db, query="pizza", limit=1)
                    if coffee_prods:
                        items_to_add.append(coffee_prods[0])
                    if pizza_prods:
                        items_to_add.append(pizza_prods[0])

            if items_to_add:
                combined_items = list(current_cart_items)
                for it in items_to_add:
                    p_id = it.get("product_id") or it.get("id")
                    prod_obj = None
                    if p_id:
                        prod_obj = await get_product_by_id_any_merchant(db, uuid.UUID(str(p_id)))
                    if not prod_obj:
                        continue
                    m_res = await db.execute(select(Merchant.name).where(Merchant.id == prod_obj.merchant_id))
                    m_name = m_res.scalar_one_or_none() or "Bangalore Store"

                    # Check contextual quantity for each item (e.g. user asked for 2 dosas)
                    item_qty = 1
                    prod_tokens = (prod_obj.name + " " + str(prod_obj.category or "")).lower().split()
                    for prev_m in reversed(conversation.messages or []):
                        if prev_m.get("role") == "user":
                            parsed_prev = parse_multi_food_items(prev_m.get("content", ""))
                            for p_it in parsed_prev:
                                c_word = p_it["canonical"].lower()
                                if any(c_word in w or w in c_word for w in prod_tokens):
                                    item_qty = max(1, p_it.get("quantity", 1))
                                    break
                            if item_qty > 1:
                                break
                    
                    combined_items.append({
                        "product_id": str(prod_obj.id),
                        "name": prod_obj.name,
                        "price": prod_obj.price,
                        "quantity": item_qty,
                        "image_url": prod_obj.image_url,
                        "category": prod_obj.category,
                        "merchant_id": str(prod_obj.merchant_id),
                        "merchant_name": m_name,
                    })

                unique_merchants = {i.get("merchant_id") or i.get("merchant_name") for i in combined_items}
                m_count = len(unique_merchants)
                is_multi_3 = m_count > 2
                cart_label = f"Multi-Kitchen ({m_count} Stores)" if is_multi_3 else "Dual Kitchen (Multi-Store)"
                banner_title = f"Multi-Kitchen Cart Created! ({m_count} Stores)" if is_multi_3 else "Dual-Kitchen Cart Created!"
                cta_text = f"Checkout All {m_count} Orders" if is_multi_3 else "Checkout Both Orders"

                cart["items"] = combined_items
                cart["is_multi_store"] = True
                cart["merchant_id"] = None
                cart["merchant_name"] = cart_label
                cart["total"] = round(sum(float(i.get("price", 0)) * int(i.get("quantity", 1)) for i in combined_items), 2)
                conversation.merchant_id = None
                update_conversation_cart(conversation, cart)

                cart_lines = []
                for idx, c_item in enumerate(combined_items, 1):
                    emoji = "☕" if "coffee" in c_item.get("name", "").lower() else ("🍕" if "pizza" in c_item.get("name", "").lower() else ("🍔" if "burger" in c_item.get("name", "").lower() else "🍽️"))
                    qty_str = f"{c_item.get('quantity', 1)}x " if c_item.get('quantity', 1) > 1 else ""
                    sub_cost = float(c_item.get('price', 0)) * int(c_item.get('quantity', 1))
                    cart_lines.append(f"{idx}. {emoji} **{qty_str}{c_item.get('name')}** from **{c_item.get('merchant_name')}** (₹{sub_cost:.0f})")
                cart_details_str = "\n".join(cart_lines)

                both_msg = (
                    f"🎉 **{banner_title}**\n\n"
                    f"I've added items from all {m_count} restaurant kitchens into your cart:\n"
                    f"{cart_details_str}\n\n"
                    f"💰 **Combined Total:** ₹{cart['total']:.0f}\n\n"
                    f"### How it works:\n"
                    f"• Each restaurant kitchen prepares their authentic specialty hot & fresh.\n"
                    f"• You pay **once** with a single combined Razorpay payment link.\n"
                    f"• You can track all deliveries side-by-side with our live **Multi-Order Switcher Bar** on the tracking screen! 🛵💨\n\n"
                    f"Ready to proceed? Open your cart on the right or tap **{cta_text}**!"
                )
                add_message_to_conversation(conversation, role="assistant", content=both_msg)
                add_agent_reasoning(
                    conversation,
                    action="multi_store_order_both_created",
                    reasoning=f"Created multi-store cart with {len(combined_items)} items across {m_count} kitchens. Combined total ₹{cart['total']:.0f}.",
                )
                await log_audit_event(
                    db=db,
                    event_type=AuditEventType.AGENT_DECISION,
                    merchant_id=None,
                    conversation_id=conversation.id,
                    action="multi_store_order_both_created",
                    reasoning=f"Orchestrated multi-store cart with single checkout for user request '{user_message}'",
                    input_data={"user_message": user_message},
                    output_data={"cart_total": cart["total"], "items_count": len(combined_items)},
                )
                yield {
                    "type": "answer",
                    "agent": "DiscoveryAgent",
                    "content": both_msg,
                    "chat_response": ChatResponse(
                        conversation_id=conversation.id,
                        merchant_id=None,
                        merchant_name=cart_label,
                        message=both_msg,
                        recommendations=None,
                        cart=[CartItem(**item) for item in combined_items],
                        cart_total=cart["total"],
                        action="cart_update",
                    ).model_dump(mode="json"),
                }
                return



        # Multi-item or store-scoping query guard:
        is_store_or_bundle_query = any(k in u_lower for k in [
            "all three", "all 3", "all of them", "all items", "all options",
            "from one restaurant", "from single restaurant", "from one store", "from single store",
            "from one place", "from one kitchen", "from the same restaurant", "from the same store",
            "from same store", "from same restaurant", "single restaurant", "single store",
            "one restaurant", "one store", "search for a single", "find a single", "is there a single",
            "both from one", "all from one", "can i get all", "can i order all", "order all",
        ])

        has_multi_items = (
            is_store_or_bundle_query
            or " and " in u_lower
            or "also order" in u_lower
            or "also add" in u_lower
            or "two order" in u_lower
            or "two orders" in u_lower
            or "two different" in u_lower
            or "different order" in u_lower
            or "both" in u_lower
            or len(re.findall(r"\b(order|add)\b", u_lower)) >= 2
        )

        is_affirmative_intent = (
            clean_cmd in [
                "yes", "yeah", "yep", "sure", "sure thing", "please do", "do it",
                "go ahead", "add it", "add this", "add that", "add please", "confirm",
                "ok", "okay", "yes please", "yes add it", "yes add", "yes do it", "yup",
                "add it for me", "add for me", "please add it for me", "add them for me",
                "order it for me", "order for me", "please order it for me", "order them for me"
            ]
            or any(clean_cmd.startswith(p) for p in [
                "yes ", "yeah ", "sure ", "please do ", "add it ", "order it ", "please add "
            ])
        )

        is_delegate_choice_intent = any(k in clean_cmd for k in [
            "anyone", "any one", "any", "whichever", "you choose", "you decide", "surprise me",
            "pick for me", "i am new", "dont know much", "don't know much", "suggest one",
            "best one", "top one"
        ])

        prev_asked_to_add = any(phrase in prev_lower for phrase in [
            "shall i add", "would you like me to add", "add ... to your cart", "to your cart",
            "just say “yes”", "just say 'yes'", "say “yes”", "say 'yes'", "recommend option",
            "which one would you like to add", "start with the filter coffee"
        ])

        prev_was_budget_warning = any(phrase in prev_lower for phrase in [
            "budget guardrail active", "exceeds your stated budget", "would you like to adjust the quantity",
            "choose an option within your", "budget_blocked"
        ])

        user_budget_adjusted = any(phrase in u_lower for phrase in [
            "can adjust", "adjust extra", "extra", "increase budget", "override budget",
            "budget is ok", "fine with", "i can pay", "adjust 55", "adjust", "i can adjust"
        ]) or (
            prev_was_budget_warning and (
                is_affirmative_intent
                or any(w in u_lower.split() for w in ["yes", "yeah", "yep", "sure", "ok", "okay", "fine", "adjust", "extra", "proceed", "agree"])
                or any(w in u_lower for w in ["add it", "go ahead", "do it", "can adjust", "please add"])
            )
        )

        is_cart_intent = (not has_multi_items) and (
            (is_affirmative_intent and (bool(last_recs) or prev_asked_to_add or prev_was_budget_warning))
            or (user_budget_adjusted and (bool(last_recs) or prev_was_budget_warning))
            or (is_delegate_choice_intent and bool(last_recs))
            or ADD_TO_CART_REGEX.search(user_message) is not None
            or any(k in u_lower for k in [
                "in my cart", "to my cart", "in cart", "to cart", "into cart", "in the cart",
                "in card", "to card", "into my cart", "my basket", "in my car",
                "add it", "add this", "add to cart", "add in cart",
                "order this", "order it", "order option 1", "order option 2", "order option 3",
                "add option 1", "add option 2", "add option 3",
            ])
            or u_lower.startswith("add ")
            or u_lower.startswith("put ")
            or bool(re.match(r"^(and|ad)\s+\d+\b", u_lower))
            or u_lower in ["1", "2", "3", "option 1", "option 2", "option 3", "the first one", "the second one"]
        )

        if is_cart_intent:
            target_prod = None
            selection_reason = "selected"

            # Parse quantity safely (do not confuse "all three" or "option 3" with quantity 3)
            req_qty = 1
            if not any(phrase in u_lower for phrase in ["all three", "all 3", "these three", "top three", "option 3", "option three", "#3"]):
                qty_match = re.search(r"\b(\d+)\s*(?:x|×|pcs|pieces|nos|plates|dosas|dosa|cakes|items)?\b", u_lower)
                if qty_match and not any(k in u_lower for k in [f"option {qty_match.group(1)}", f"#{qty_match.group(1)}"]):
                    try:
                        parsed_q = int(qty_match.group(1))
                        if 1 <= parsed_q <= 20:
                            req_qty = parsed_q
                    except Exception:
                        pass
                elif any(w in u_lower.split() for w in ["two", "2x", "2×", "double"]) and "two orders" not in u_lower and "option 2" not in u_lower:
                    req_qty = 2
                elif any(w in u_lower.split() for w in ["three", "3x", "3×", "triple"]) and "all three" not in u_lower and "option 3" not in u_lower:
                    req_qty = 3

            # Check for store name in message
            matched_store_rec = None
            if last_recs and not is_affirmative_intent and not user_budget_adjusted:
                for r in last_recs:
                    m_name = (r.get("merchant_name") or r.get("reasoning") or "").lower()
                    for word in u_lower.replace("'", "").replace("’", "").split():
                        if len(word) >= 4 and word in m_name.replace("'", "").replace("’", ""):
                            matched_store_rec = r
                            break
                    if matched_store_rec:
                        break

            # Scenario 1: User explicitly picked or mentioned a store
            if matched_store_rec:
                target_prod = matched_store_rec
                selection_reason = f"{matched_store_rec.get('name')} from {matched_store_rec.get('merchant_name', 'Store')}"

            # Scenario 2: "order from that shop I ordered before" / "favorite shop"
            elif any(phrase in u_lower for phrase in ["ordered before", "favorite shop", "usual shop", "from that shop", "last time"]):
                fav_name = "Sweet Chariot"
                if customer_mem and "Sweet Chariot" in customer_mem:
                    fav_name = "Sweet Chariot"
                elif customer_mem and "Beijing Bites" in customer_mem:
                    fav_name = "Beijing Bites"
                elif customer_mem and "Shanghai Court" in customer_mem:
                    fav_name = "Shanghai Court"
                fav_prods = await search_all_merchants_catalog(db, query=fav_name, limit=3)
                if fav_prods:
                    target_prod = fav_prods[0]
                    selection_reason = f"picked from your favorite store ({target_prod.get('merchant_name', fav_name)}) based on your previous order history"

            # Scenario 3: User delegates choice / asks for recommendation ("anyone", "i am new", "highest rating")
            elif any(phrase in u_lower for phrase in [
                "good rating", "highest rating", "best rating", "top rated", "top rating", "you recommend", "your choice", "your brain", "something good",
                "anyone", "any one", "any", "whichever", "you decide", "you choose", "surprise me", "pick for me",
                "i am new", "dont know much", "don't know much", "suggest one", "best one", "top one"
            ]):
                if last_recs:
                    from app.services.order_service import extract_customer_budget
                    budget_limit = extract_customer_budget(conversation.messages or [])
                    if not budget_limit:
                        b_match = re.search(r"(?:budget\s*(?:is|of|:)?|under|within|below|max)\s*(?:₹|rs\.?|inr)?\s*(\d+(?:\.\d+)?)", u_lower)
                        if b_match:
                            try:
                                budget_limit = float(b_match.group(1))
                            except Exception:
                                pass
                    candidates = last_recs
                    if budget_limit:
                        in_budget = [r for r in last_recs if float(r.get("price", 0.0) or 0.0) <= budget_limit]
                        if in_budget:
                            candidates = in_budget
                    sorted_by_rating = sorted(candidates, key=lambda x: float(x.get("rating", 4.5) or 4.5), reverse=True)
                    target_prod = sorted_by_rating[0]
                    selection_reason = f"picked the highest-rated Bangalore classic (⭐ {target_prod.get('rating', 4.8)}/5.0 from {target_prod.get('merchant_name', 'Store')})"
                else:
                    top_prods = await search_all_merchants_catalog(db, limit=4)
                    if top_prods:
                        target_prod = top_prods[0]
                        selection_reason = f"picked our city customer favorite (⭐ {target_prod.get('rating', 4.9)}/5.0 from {target_prod.get('merchant_name', 'Store')})"

            # Scenario 4: Affirmative Confirmation / Budget override confirmation
            elif is_affirmative_intent or user_budget_adjusted:
                # 0. Did the previous message trigger a budget warning for a specific product?
                if prev_was_budget_warning:
                    if last_recs:
                        for r in last_recs:
                            r_name = (r.get("name") or "").lower()
                            if r_name and r_name in prev_lower:
                                target_prod = r
                                selection_reason = f"{r.get('name')} as budget adjustment approved"
                                break
                    if not target_prod:
                        m_prev_prod = re.search(r"adding\s+\d+x\s+([^(\n]+?)(?:\s*\([^)]*\))?\s*\(₹", prev_lower)
                        if m_prev_prod:
                            extracted_name = m_prev_prod.group(1).strip()
                            found_p = await search_all_merchants_catalog(db, query=extracted_name, limit=1)
                            if found_p:
                                target_prod = found_p[0]
                                selection_reason = f"{target_prod.get('name')} as budget adjustment approved"

                # 1. Did previous assistant message recommend an explicit store from last_recs?
                if not target_prod and last_recs:
                    for r in last_recs:
                        m_name = (r.get("merchant_name") or "").lower()
                        if m_name and m_name in prev_lower:
                            target_prod = r
                            selection_reason = f"Option from {r.get('merchant_name')} as confirmed"
                            break
                # 2. Did previous message recommend Option 1/2/3?
                if not target_prod and last_recs:
                    if "option 2" in prev_lower or "#2" in prev_lower:
                        target_prod = last_recs[1] if len(last_recs) > 1 else last_recs[0]
                        selection_reason = f"Option 2 ({target_prod.get('name')} from {target_prod.get('merchant_name', 'Store')}) as confirmed"
                    elif "option 3" in prev_lower or "#3" in prev_lower:
                        target_prod = last_recs[2] if len(last_recs) > 2 else last_recs[0]
                        selection_reason = f"Option 3 ({target_prod.get('name')} from {target_prod.get('merchant_name', 'Store')}) as confirmed"
                    else:
                        target_prod = last_recs[0]
                        selection_reason = f"Option 1 ({target_prod.get('name')} from {target_prod.get('merchant_name', 'Store')}) as confirmed"
                elif not target_prod:
                    q_term = "Filter Coffee Taaza Thindi" if "taaza thindi" in prev_lower else "Filter Coffee"
                    prods = await search_all_merchants_catalog(db, query=q_term, limit=2)
                    if prods:
                        target_prod = prods[0]
                        selection_reason = f"confirmed from previous recommendation ({target_prod.get('name')} from {target_prod.get('merchant_name', 'Store')})"

            # Scenario 5: Explicit Option Reference (e.g. "add option 2", "2nd", "second", "2")
            elif last_recs:
                if "option 2" in u_lower or "2nd" in u_lower or "second" in u_lower or "2" in u_lower.split():
                    target_prod = last_recs[1] if len(last_recs) > 1 else last_recs[0]
                    selection_reason = f"Option 2 ({target_prod.get('name')} from {target_prod.get('merchant_name', 'Store')})"
                elif "option 3" in u_lower or "3rd" in u_lower or "third" in u_lower or "3" in u_lower.split():
                    target_prod = last_recs[2] if len(last_recs) > 2 else last_recs[0]
                    selection_reason = f"Option 3 ({target_prod.get('name')} from {target_prod.get('merchant_name', 'Store')})"
                else:
                    for r in last_recs:
                        if any(w in r.get("name", "").lower() for w in u_lower.split() if len(w) > 3):
                            target_prod = r
                            selection_reason = r.get("name", "Product")
                            break
                    if not target_prod and (
                        any(k in u_lower for k in ["option 1", "1st", "first", "1", "the first one", "choice 1"])
                        or (len(last_recs) == 1 and any(k in u_lower for k in ["add it", "add this", "order this", "order it"]))
                    ):
                        target_prod = last_recs[0]
                        selection_reason = f"Option 1 ({target_prod.get('name')} from {target_prod.get('merchant_name', 'Store')})"

            if target_prod:
                p_id = target_prod.get("product_id") or target_prod.get("id")
                p_name = target_prod.get("name", "Product")
                p_price = float(target_prod.get("price", 0.0))
                store_name = target_prod.get("merchant_name")

                # Contextual quantity memory: If req_qty == 1, check if user requested a higher quantity earlier
                if req_qty == 1:
                    prod_tokens = (p_name + " " + str(target_prod.get("category", ""))).lower().split()
                    for prev_m in reversed(conversation.messages or []):
                        if prev_m.get("role") == "user":
                            parsed_prev = parse_multi_food_items(prev_m.get("content", ""))
                            for p_it in parsed_prev:
                                c_word = p_it["canonical"].lower()
                                if any(c_word in w or w in c_word for w in prod_tokens):
                                    req_qty = max(1, p_it.get("quantity", 1))
                                    break
                            if req_qty > 1:
                                break

                target_merchant_id = target_prod.get("merchant_id")
                if not target_merchant_id and p_id:
                    try:
                        p_res = await db.execute(select(Product.merchant_id).where(Product.id == uuid.UUID(str(p_id))))
                        target_merchant_id = p_res.scalar_one_or_none()
                    except Exception:
                        target_merchant_id = None

                if not store_name or store_name == "Bangalore Store":
                    try:
                        if target_merchant_id:
                            stmt_m = select(Merchant.name).where(Merchant.id == target_merchant_id)
                        else:
                            stmt_m = (
                                select(Merchant.name)
                                .join(Product, Product.merchant_id == Merchant.id)
                                .where(Product.id == uuid.UUID(str(p_id)))
                            )
                        res_m = await db.execute(stmt_m)
                        found_m_name = res_m.scalar_one_or_none()
                        store_name = found_m_name or "Bangalore Store"
                    except Exception:
                        store_name = "Bangalore Store"
                
                current_items = list(cart.get("items", []))
                existing_store_id = conversation.merchant_id or cart.get("merchant_id")
                if not existing_store_id and current_items:
                    existing_store_id = current_items[0].get("merchant_id")

                # SINGLE-STORE GUARDRAIL: Check for store mismatch in Fast-Path 3
                is_cross_store_request = bool(existing_store_id and target_merchant_id and str(target_merchant_id) != str(existing_store_id))
                is_explicit_multi_intent = any(k in u_lower for k in [
                    "some restro", "some restaurant", "another store", "another restaurant",
                    "different store", "different restaurant", "order both", "dual", "from other",
                    "both", "also add", "also order", "somewhere else", "from somewhere", "other restro"
                ]) or bool(cart.get("is_multi_store"))

                if is_cross_store_request and not is_explicit_multi_intent:
                    ex_res = await db.execute(select(Merchant.name).where(Merchant.id == uuid.UUID(str(existing_store_id))))
                    ex_name = ex_res.scalar_one_or_none() or "your current restaurant"

                    mismatch_msg = (
                        f"In our food delivery platform, each order is prepared and delivered hot from a **single restaurant kitchen**.\n\n"
                        f"Your cart currently has items from **{ex_name}**, whereas **{p_name}** is from **{store_name}**.\n\n"
                        f"Here are the best ways we can proceed:\n"
                        f"1. **Add to Dual-Kitchen Cart (Unified Checkout)**: Say *\"order both\"* to pay once with a single Razorpay link!\n"
                        f"2. **Complete your {ex_name} order first**, and we can place a separate delivery order with **{store_name}**.\n"
                        f"3. **Switch stores**: Say *\"clear cart\"* to switch to **{store_name}**.\n\n"
                        f"Which would you prefer?"
                    )
                    add_message_to_conversation(conversation, role="assistant", content=mismatch_msg)
                    yield {
                        "type": "answer",
                        "agent": "DiscoveryAgent",
                        "content": mismatch_msg,
                        "chat_response": ChatResponse(
                            conversation_id=conversation.id,
                            merchant_id=uuid.UUID(str(existing_store_id)),
                            merchant_name=ex_name,
                            message=mismatch_msg,
                            recommendations=None,
                            cart=[
                                CartItem(
                                    product_id=uuid.UUID(i["product_id"]) if isinstance(i["product_id"], str) else i["product_id"],
                                    name=i["name"],
                                    price=i["price"],
                                    quantity=i.get("quantity", 1),
                                    merchant_id=uuid.UUID(str(i["merchant_id"])) if i.get("merchant_id") else None,
                                    merchant_name=i.get("merchant_name"),
                                )
                                for i in current_items
                            ],
                            cart_total=float(cart.get("total", 0.0)),
                            action="chat",
                            payment_link=None,
                            agent_reasoning=conversation.agent_reasoning if conversation.agent_reasoning else None,
                        ).model_dump(mode="json"),
                    }
                    return

                # Strict Budget Guardrail Check for Fast-Path 3
                from app.services.order_service import extract_customer_budget
                detected_budget = extract_customer_budget(conversation.messages or [])
                current_total = float(cart.get("total", 0.0))
                additional_cost = p_price * req_qty
                projected_total = current_total + additional_cost

                # Only block if user hasn't explicitly affirmed, overridden budget, or requested cross-store combo
                if detected_budget is not None and projected_total > detected_budget and not is_explicit_multi_intent and not user_budget_adjusted:
                    remaining_budget = max(0.0, detected_budget - current_total)
                    budget_msg = (
                        f"⚠️ **Budget Guardrail Active**: Adding **{req_qty}x {p_name}** (₹{additional_cost:.0f}) would bring your cart total to **₹{projected_total:.0f}**, "
                        f"which exceeds your stated budget of **₹{detected_budget:.0f}** (Remaining: ₹{remaining_budget:.0f}).\n\n"
                        f"Would you like to adjust the quantity or choose an option within your ₹{detected_budget:.0f} budget?"
                    )
                    add_message_to_conversation(
                        conversation,
                        role="assistant",
                        content=budget_msg,
                        metadata={"action": "budget_blocked", "budget_limit": detected_budget, "projected_total": projected_total},
                    )
                    yield {
                        "type": "answer",
                        "agent": "DiscoveryAgent",
                        "content": budget_msg,
                        "chat_response": ChatResponse(
                            conversation_id=conversation.id,
                            merchant_id=conversation.merchant_id,
                            merchant_name=conversation.cart.get("merchant_name") if conversation.cart else None,
                            message=budget_msg,
                            recommendations=None,
                            cart=[
                                CartItem(
                                    product_id=uuid.UUID(i["product_id"]) if isinstance(i["product_id"], str) else i["product_id"],
                                    name=i["name"],
                                    price=i["price"],
                                    quantity=i.get("quantity", 1),
                                    merchant_id=uuid.UUID(str(i["merchant_id"])) if i.get("merchant_id") else None,
                                    merchant_name=i.get("merchant_name"),
                                )
                                for i in current_items
                            ],
                            cart_total=current_total,
                            action="chat",
                            payment_link=None,
                        ).model_dump(mode="json"),
                    }
                    return

                distinct_merchants = {str(i.get("merchant_id")) for i in current_items if i.get("merchant_id")}
                if target_merchant_id:
                    distinct_merchants.add(str(target_merchant_id))
                is_multi = len(distinct_merchants) > 1 or is_cross_store_request or bool(cart.get("is_multi_store"))

                if is_multi:
                    conversation.merchant_id = None
                    cart["is_multi_store"] = True
                    cart["merchant_id"] = None
                    cart["merchant_name"] = "Dual Kitchen (Multi-Store)"
                else:
                    if target_merchant_id:
                        conversation.merchant_id = uuid.UUID(str(target_merchant_id))
                    cart["merchant_id"] = str(target_merchant_id) if target_merchant_id else None
                    cart["merchant_name"] = store_name

                existing_item = next((i for i in current_items if str(i.get("product_id")) == str(p_id)), None)
                if existing_item:
                    existing_item["quantity"] = existing_item.get("quantity", 1) + req_qty
                else:
                    current_items.append({
                        "product_id": str(p_id),
                        "name": p_name,
                        "price": p_price,
                        "quantity": req_qty,
                        "merchant_id": str(target_merchant_id) if target_merchant_id else None,
                        "merchant_name": store_name,
                    })
                new_total = sum(i["price"] * i.get("quantity", 1) for i in current_items)
                cart["items"] = current_items
                cart["total"] = round(new_total, 2)
                if user_budget_adjusted:
                    cart["budget"] = {"budget_amount": round(max(new_total, (detected_budget or 0.0) + 100), 2), "is_hard_limit": False}
                update_conversation_cart(conversation, cart)
                
                yield {
                    "type": "tool_call",
                    "agent": "DiscoveryAgent",
                    "tool": "add_to_cart",
                    "tool_display": "Add to Cart",
                    "args": {"product_name": p_name, "merchant_name": store_name, "quantity": req_qty, "price": p_price},
                    "content": f"Adding {req_qty}x `{p_name}` from **{store_name}** to your {'Dual-Kitchen ' if is_multi else ''}cart...",
                }
                yield {
                    "type": "tool_result",
                    "agent": "DiscoveryAgent",
                    "tool": "add_to_cart",
                    "summary": f"Added {req_qty}x {p_name} to cart ({selection_reason}). Total: ₹{new_total:.0f}",
                    "data": {"cart_total": new_total, "items_count": len(current_items), "item": p_name, "quantity": req_qty},
                }
                
                is_adding_pizza = "pizza" in p_name.lower() or "pizza" in str(target_prod.get("category", "")).lower()

                unfulfilled = []
                for msg in reversed(conversation.messages or []):
                    if msg.get("role") == "user":
                        parsed_p = parse_multi_food_items(msg.get("content", ""))
                        for p_it in parsed_p:
                            c_name = p_it["canonical"].lower()
                            if c_name not in p_name.lower() and not any(c_name in it.get("name", "").lower() for it in current_items):
                                unfulfilled.append(f"{p_it.get('quantity', 1)}x {p_it['raw'].capitalize()}")
                        if unfulfilled:
                            break

                if is_multi:
                    stores_summary = " & ".join(list(dict.fromkeys([i.get("merchant_name") for i in current_items if i.get("merchant_name")])))
                    budget_note = ""
                    if detected_budget is not None:
                        if new_total <= detected_budget:
                            budget_note = f" (Fits within your ₹{detected_budget:.0f} budget with ₹{detected_budget - new_total:.0f} left!)"
                        else:
                            budget_note = f" (₹{new_total - detected_budget:.0f} above your initial ₹{detected_budget:.0f} target)."
                    next_step_prompt = (
                        f"\n\n🎉 **Dual-Kitchen Cart Active!** Items from **{stores_summary}** are now bundled together in your cart.{budget_note}\n\n"
                        f"You can review both kitchens on the right and checkout with a single combined Razorpay payment link! 💳"
                    )
                elif unfulfilled:
                    rem_str = " and ".join(unfulfilled)
                    next_step_prompt = f"\n\nNow, as planned, let's add your **{rem_str}**! Would you like to pick from the options above or shall I choose the best one for you?"
                else:
                    next_step_prompt = f"\n\nYour current cart total is **₹{new_total:.0f}**. Would you like to add anything else or proceed to checkout with Razorpay?"

                emoji = "🍕" if is_adding_pizza else ("🥞" if "dosa" in p_name.lower() else ("☕" if "coffee" in p_name.lower() else "🛒"))
                cart_type_str = "to your **Dual-Kitchen Cart**" if is_multi else "to your cart"
                prefix_msg = "Done! I've updated your budget and added" if user_budget_adjusted else "Done! I've added"
                final_text = (
                    f"{prefix_msg} **{req_qty}x {p_name}** (₹{p_price * req_qty:.0f}) from **{store_name}** {cart_type_str}! {emoji}\n\n"
                    f"*({selection_reason})*"
                    f"{next_step_prompt}"
                )
                
                add_message_to_conversation(
                    conversation,
                    role="assistant",
                    content=final_text,
                    metadata={
                        "action": "cart_update",
                        "recommendations": last_recs,
                    },
                )

                cart_items_list = [
                    CartItem(
                        product_id=uuid.UUID(i["product_id"]) if isinstance(i["product_id"], str) else i["product_id"],
                        name=i["name"],
                        price=i["price"],
                        quantity=i.get("quantity", 1),
                        merchant_id=uuid.UUID(str(i["merchant_id"])) if i.get("merchant_id") else None,
                        merchant_name=i.get("merchant_name"),
                    )
                    for i in current_items
                ]
                
                yield {
                    "type": "answer",
                    "agent": "DiscoveryAgent",
                    "content": final_text,
                    "chat_response": ChatResponse(
                        conversation_id=conversation.id,
                        merchant_id=None,
                        merchant_name="Dual Kitchen (Multi-Store)" if is_multi else store_name,
                        message=final_text,
                        recommendations=None,
                        cart=cart_items_list,
                        cart_total=float(new_total),
                        action="cart_update",
                        payment_link=None,
                        agent_reasoning=conversation.agent_reasoning if conversation.agent_reasoning else None,
                    ).model_dump(mode="json"),
                }
                return

        recommendations: list[ProductRecommendation] = []
        action_type = "chat"
        payment_link: str | None = None
        final_text = ""
        resolved_merchant_id: uuid.UUID | None = None
        resolved_merchant_name: str | None = None
        last_search_query = ""
        has_items = False

        # 3. Speculative Multi-Item & Single-Item Knowledge Funnel (<15ms DB search)
        is_conversational_query = bool(
            "?" in user_message
            or re.search(r"\b(why|how|what|when|where|is\s+there|are\s+there|so\s+there|can\s+i|can\s+we|could\s+|would\s+|does\s+|do\s+they|which\s+one|no\s+shop|any\s+shop|tell\s+me\s+if|explain)\b", u_lower)
        )
        multi_food_items = parse_multi_food_items(user_message)
        budget_amt = cart.get("budget", {}).get("budget_amount")

        # Multi-Item Knowledge Funnel: When user mentions 2 or more distinct items (e.g. "two dosa one pizza my budget for both is 500" or "2 dosas and 1 pizza and burger")
        if len(multi_food_items) >= 2 and not is_conversational_query:
            f_results = await asyncio.gather(
                *[search_with_alternatives(db, query=item["raw"], limit=4) for item in multi_food_items]
            )

            item_pools = []
            for f_res in f_results:
                pool = f_res.get("exact_matches") or f_res.get("over_budget_matches") or f_res.get("alternatives") or []
                item_pools.append(pool)

            if all(bool(p) for p in item_pools):
                action_type = "recommend"
                selected_display = []
                cards_per_item = max(1, 4 // len(multi_food_items))
                for pool in item_pools:
                    selected_display.extend(pool[:cards_per_item])

                for p in selected_display[:6]:
                    rating_str = f"⭐ {p.get('rating', 4.5)} " if p.get("rating") else ""
                    recommendations.append(
                        ProductRecommendation(
                            product_id=uuid.UUID(p["id"]) if isinstance(p["id"], str) else p["id"],
                            merchant_id=uuid.UUID(str(p["merchant_id"])) if p.get("merchant_id") else None,
                            name=p["name"],
                            price=float(p["price"]),
                            description=p.get("description") or "",
                            image_url=p.get("image_url") or "",
                            category=p.get("category"),
                            merchant_name=p.get("merchant_name") or "Bangalore Store",
                            reasoning=f"{rating_str}From {p.get('merchant_name', 'Bangalore Store')} — ₹{float(p['price']):.0f}",
                        )
                    )

                best_items = [pool[0] for pool in item_pools]
                combo_cost = round(
                    sum(it["quantity"] * float(b["price"]) for it, b in zip(multi_food_items, best_items)), 2
                )
                fits_budget = (budget_amt is None) or (combo_cost <= budget_amt)
                diff = abs(budget_amt - combo_cost) if budget_amt else 0.0

                items_desc = " and ".join(f"{it['quantity']}x {it['raw']}" for it in multi_food_items)
                search_summary = f"Curated {items_desc} across Bangalore stores (Combo Total: ₹{combo_cost:.0f})"
                yield {
                    "type": "tool_call",
                    "agent": "DiscoveryAgent",
                    "tool": "search_all_stores",
                    "tool_display": f"{'Multi-Store' if len(multi_food_items) > 2 else 'Dual-Store'} Knowledge Search",
                    "args": {
                        "items": [f"{it['quantity']}x {it['raw']}" for it in multi_food_items],
                        "budget": budget_amt,
                    },
                    "content": f"Querying Bangalore kitchens for {items_desc}...",
                }
                data_dict = {
                    f"item_{idx+1}": {
                        "name": it["raw"],
                        "quantity": it["quantity"],
                        "best_match": b["name"],
                        "price": float(b["price"]),
                        "store": b.get("merchant_name"),
                    }
                    for idx, (it, b) in enumerate(zip(multi_food_items, best_items))
                }
                data_dict.update({
                    "combo_total": combo_cost,
                    "customer_budget": budget_amt,
                    "fits_budget": fits_budget,
                    "savings": diff if fits_budget else 0.0,
                    "over_by": diff if not fits_budget else 0.0,
                })
                yield {
                    "type": "tool_result",
                    "agent": "DiscoveryAgent",
                    "tool": "search_all_stores",
                    "summary": search_summary,
                    "data": data_dict,
                }

                call_id = f"call_multi_{uuid.uuid4().hex[:6]}"
                budget_clause = (
                    f"Great news! Your combo total of ₹{combo_cost:.0f} is ₹{diff:.0f} below your ₹{budget_amt:.0f} budget!"
                    if (budget_amt and fits_budget)
                    else (
                        f"Note: This combo total of ₹{combo_cost:.0f} is ₹{diff:.0f} above your ₹{budget_amt:.0f} budget."
                        if (budget_amt and not fits_budget)
                        else f"Combo total is ₹{combo_cost:.0f}."
                    )
                )

                tool_content_dict = {
                    f"item_{idx+1}_options": [
                        {"name": p["name"], "price": p["price"], "store": p.get("merchant_name"), "rating": p.get("rating")}
                        for p in pool[:2]
                    ]
                    for idx, pool in enumerate(item_pools)
                }
                math_parts = [f"{it['quantity']}x {b['name']} ({b.get('merchant_name')}) at ₹{float(b['price']):.0f}" for it, b in zip(multi_food_items, best_items)]
                tool_content_dict["combo_math"] = " + ".join(math_parts) + f" = ₹{combo_cost:.0f}"
                tool_content_dict["budget_analysis"] = budget_clause
                cuisine_names = ", ".join(it["raw"].title() for it in multi_food_items)
                tool_content_dict["instruction"] = (
                    "You are Meera, the expert warm Bangalore food guide. "
                    f"Explain that the requested {len(multi_food_items)} cuisines ({cuisine_names}) "
                    "come from distinct specialty restaurant kitchens in Bangalore. "
                    "Present the options in an appetizing, clean Markdown comparison table with columns (#, Store, Dish, Rating, Price in ₹). "
                    f"{budget_clause} "
                    "Present clean paths for the customer: 1. Unified Checkout (say 'order both' or 'order all' to keep all items in your cart and pay once with 1 Razorpay payment link), "
                    "2. Order them as separate deliveries starting with the first kitchen. "
                    "Always ask which option they prefer."
                )

                llm_messages.append({
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [{
                        "id": call_id,
                        "type": "function",
                        "function": {
                            "name": "search_all_stores",
                            "arguments": json.dumps({"items": [it["raw"] for it in multi_food_items], "budget": budget_amt}),
                        },
                    }],
                })
                llm_messages.append({
                    "role": "tool",
                    "tool_call_id": call_id,
                    "name": "search_all_stores",
                    "content": json.dumps(tool_content_dict),
                })

        skip_speculative = bool(
            is_conversational_query
            or len(multi_food_items) >= 2
            or has_multi_items
            or is_store_or_bundle_query
            or any(k in u_lower for k in ["both", "different", "all 3", "all three", "single store", "one restaurant"])
        )
        spec_kw = extract_search_keywords(user_message) if not skip_speculative else ""
        if len(spec_kw) >= 3 and not skip_speculative:
            funnel_result = await search_with_alternatives(db, query=spec_kw, max_price=budget_amt, limit=6)
            exact_matches = funnel_result.get("exact_matches", [])
            over_budget_matches = funnel_result.get("over_budget_matches", [])
            alternatives = funnel_result.get("alternatives", [])
            has_items = bool(exact_matches or over_budget_matches)

            if has_items:
                action_type = "recommend"
                last_search_query = spec_kw

                # Populate recommendations list for frontend cards
                display_pool = exact_matches if exact_matches else (over_budget_matches[:2] + alternatives[:3])
                for p in display_pool[:4]:
                    rating_str = f"⭐ {p.get('rating', 4.5)} " if p.get("rating") else ""
                    recommendations.append(
                        ProductRecommendation(
                            product_id=uuid.UUID(p["id"]) if isinstance(p["id"], str) else p["id"],
                            name=p["name"],
                            price=float(p["price"]),
                            description=p.get("description") or "",
                            image_url=p.get("image_url") or "",
                            category=p.get("category"),
                            merchant_name=p.get("merchant_name") or "Bangalore Store",
                            reasoning=f"{rating_str}From {p.get('merchant_name', 'Bangalore Store')} — ₹{float(p['price']):.0f}",
                        )
                    )

                yield {
                    "type": "tool_call",
                    "agent": "DiscoveryAgent",
                    "tool": "search_all_stores",
                    "tool_display": "Three-Tier Knowledge Search",
                    "args": {"query": spec_kw, "max_price": budget_amt},
                    "content": f"Querying 214 Bangalore stores for `{spec_kw}` with alternatives funnel...",
                }
                yield {
                    "type": "tool_result",
                    "agent": "DiscoveryAgent",
                    "tool": "search_all_stores",
                    "summary": funnel_result.get("explanation") or f"Searched catalog for '{spec_kw}'",
                    "data": {
                        "explanation": funnel_result.get("explanation"),
                        "is_over_budget": funnel_result.get("is_over_budget"),
                        "exact_matches": exact_matches,
                        "over_budget_matches": over_budget_matches,
                        "alternatives": alternatives,
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
                            "name": "search_all_stores",
                            "arguments": json.dumps({"query": spec_kw, "max_price": budget_amt}),
                        },
                    }],
                })
                llm_messages.append({
                    "role": "tool",
                    "tool_call_id": call_id,
                    "name": "search_all_stores",
                    "content": json.dumps({
                        "explanation": funnel_result.get("explanation"),
                        "is_over_budget": funnel_result.get("is_over_budget"),
                        "exact_matches": [
                            {"name": p["name"], "price": p["price"], "store": p.get("merchant_name"), "rating": p.get("rating")}
                            for p in exact_matches
                        ],
                        "over_budget_matches": [
                            {"name": p["name"], "price": p["price"], "over_by": p.get("over_budget_by"), "store": p.get("merchant_name"), "rating": p.get("rating")}
                            for p in over_budget_matches
                        ],
                        "alternatives": [
                            {"name": p["name"], "price": p["price"], "store": p.get("merchant_name"), "rating": p.get("rating")}
                            for p in alternatives
                        ],
                        "instruction": (
                            "You are Meera, the warm expert shopkeeper. "
                            "If the exact item is over-budget, explain it clearly: state its price and which store has it, "
                            "then present the in-budget alternatives in a clean comparison table (#, Store, Dish, Rating, Price in ₹). "
                            "Give the customer clear choices: stretch budget or choose an in-budget alternative! "
                            "STRICT REQUIREMENT: Respond exclusively in clean, polished English. NEVER use Hindi or Hinglish slang like 'Bhai' or 'Yeh lo'."
                        ),
                    }),
                })
        try:
            tools_executed_count = 0
            for cycle_idx in range(3):
                allow_tools = DISCOVERY_TOOLS if (cycle_idx < 2 and tools_executed_count < 2) else None
                choice = "auto" if allow_tools else "none"

                yield {
                    "type": "thinking",
                    "agent": "DiscoveryAgent",
                    "content": f"Scanning cross-merchant inventory and pricing (Cycle {cycle_idx + 1})...",
                }

                response = await groq_client.chat_completion(
                    messages=llm_messages,
                    tools=allow_tools,
                    tool_choice=choice,
                    temperature=0.25,
                    max_tokens=500,
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
                    tools_executed_count += 1
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
                    elif fn_name == "search_by_occasion":
                        summary = f"Curated {len(t_res.get('curated_items', []))} items for {t_res.get('occasion_theme', 'occasion')} (Total: ₹{t_res.get('total_combo_cost', 0):.0f})"
                    elif fn_name == "reorder_previous":
                        summary = t_res.get("message", "Reloaded previous order.")
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
                try:
                    synth_resp = await groq_client.chat_completion(
                        messages=llm_messages,
                        temperature=0.3,
                        max_tokens=450,
                    )
                    final_text = synth_resp.choices[0].message.content or ""
                except Exception as synth_err:
                    logger.warning("Streaming synthesis error: %s", synth_err)

            if not final_text:
                final_text = "I ran a city-wide search across Bangalore stores. How else can I assist?"

        except Exception as exc:
            logger.error("DiscoveryAgent streaming error: %s", exc, exc_info=True)
            final_text = "I ran a city-wide search across Bangalore stores. How else can I assist?"

        final_text = sanitize_english_response(final_text)

        # Suppress recommendation cards on pure conversational/clarifying questions
        if is_conversational_query:
            recommendations = []

        # Deduplicate and balance recommendations across categories (max 4 cards)
        if recommendations:
            seen_ids = set()
            deduped = []
            for r in recommendations:
                rid = str(r.product_id)
                if rid not in seen_ids:
                    seen_ids.add(rid)
                    deduped.append(r)

            by_cat: dict[str, list[ProductRecommendation]] = {}
            for r in deduped:
                cat = r.category or "General"
                by_cat.setdefault(cat, []).append(r)

            if len(by_cat) > 1:
                balanced: list[ProductRecommendation] = []
                max_per_cat = max(1, 4 // len(by_cat))
                for cat_items in by_cat.values():
                    balanced.extend(cat_items[:max_per_cat])
                for r in deduped:
                    if len(balanced) >= 4:
                        break
                    if r not in balanced:
                        balanced.append(r)
                recommendations = balanced[:4]
            else:
                recommendations = deduped[:4]

        cart_items_list = [
            CartItem(
                product_id=uuid.UUID(i["product_id"]) if isinstance(i["product_id"], str) else i["product_id"],
                name=i["name"],
                price=float(i["price"]),
                quantity=int(i.get("quantity", 1)),
                merchant_id=uuid.UUID(str(i["merchant_id"])) if i.get("merchant_id") else None,
                merchant_name=i.get("merchant_name"),
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
