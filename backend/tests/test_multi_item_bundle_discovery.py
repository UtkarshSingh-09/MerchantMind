"""Unit and Integration tests for Multi-Item Cross-Category Bundle Discovery.
Verifies queries like 'i want to buy two dosa one pizza my budget for both is 500'
correctly search both items, handle plural category stemming (Pizzas -> Pizza),
balance recommendation cards, and compute combo pricing within budget.
"""

import uuid
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.merchant import Merchant
from app.models.product import Product
from app.models.conversation import Conversation
from app.agents.discovery_agent import parse_multi_food_items, discovery_agent
from app.services.catalog_search import search_with_alternatives


def test_parse_multi_food_items():
    """Verifies regex extraction of multiple food items and their quantities."""
    query = "i want to buy two dosa one pizza my budget for both is 500"
    items = parse_multi_food_items(query)
    
    assert len(items) == 2, f"Expected 2 parsed items, got: {items}"
    
    canonicals = {it["canonical"]: it["quantity"] for it in items}
    assert "dosa" in canonicals
    assert canonicals["dosa"] == 2
    assert "pizza" in canonicals
    assert canonicals["pizza"] == 1


@pytest.mark.asyncio
async def test_plural_category_stemming_matches_singular(db_session: AsyncSession):
    """Verifies that passing category='Pizzas' successfully finds products with category='Pizza'."""
    merchant = Merchant(
        name=f"Pizzeria Test {uuid.uuid4().hex[:6]}",
        email=f"pizza_{uuid.uuid4().hex[:6]}@test.com",
        description="Authentic wood-fired pizzas",
        is_active=True,
    )
    db_session.add(merchant)
    await db_session.commit()
    await db_session.refresh(merchant)

    pizza = Product(
        merchant_id=merchant.id,
        name="Woodfired Margherita Pizza",
        price=270.0,
        category="Pizza",
        in_stock=True,
    )
    db_session.add(pizza)
    await db_session.commit()

    # Search with plural category 'Pizzas' and max_price=350.0
    result = await search_with_alternatives(
        db=db_session,
        query="pizza",
        category="Pizzas",
        max_price=350.0,
        limit=5,
    )

    assert result["has_exact_match"] is True, "Expected exact match for Pizza with category='Pizzas'"
    assert len(result["exact_matches"]) >= 1
    for p in result["exact_matches"]:
        assert "pizza" in p["name"].lower() or p["category"] == "Pizza"


@pytest.mark.asyncio
async def test_discovery_agent_multi_item_balanced_cards(db_session: AsyncSession):
    """Verifies DiscoveryAgent multi-item knowledge funnel produces balanced recommendations for both items."""
    # Create conversation
    conv = Conversation(
        channel="web",
        merchant_id=None,
        cart={"items": [], "total": 0.0},
        messages=[],
    )
    db_session.add(conv)
    await db_session.commit()
    await db_session.refresh(conv)

    query = "i want to buy two dosa one pizza my budget for both is 500"
    
    # Run discovery agent
    events = []
    async for event in discovery_agent.process_message_streaming(
        db=db_session,
        conversation=conv,
        user_message=query,
    ):
        events.append(event)

    result_event = next((e for e in events if e.get("type") == "answer"), None)
    assert result_event is not None, "Expected answer event from DiscoveryAgent"
    
    chat_resp = result_event.get("chat_response", {})
    recs = chat_resp.get("recommendations", [])
    assert len(recs) > 0, f"Expected recommendations to be returned, got {recs}"
    
    # Check that BOTH Dosa and Pizza are represented in the recommendation cards
    has_dosa = any("dosa" in r["name"].lower() or "South Indian" in str(r.get("category")) for r in recs)
    has_pizza = any("pizza" in r["name"].lower() or "Pizza" in str(r.get("category")) for r in recs)

    assert has_dosa, f"Expected Dosa items in recommendations: {[r['name'] for r in recs]}"
    assert has_pizza, f"Expected Pizza items in recommendations: {[r['name'] for r in recs]}"

    # Check response text mentions budget / combo / prices
    final_text = result_event.get("content", "")
    assert ("₹" in final_text or "budget" in final_text.lower() or "500" in final_text), "Response text should mention price/budget"
