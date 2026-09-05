
"""Tests for Single-Restaurant Multi-Item Guardrails and Agentic Fulfillment."""

import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.merchant import Merchant
from app.models.product import Product
from app.models.conversation import Conversation
from app.agents.discovery_agent import discovery_agent


@pytest.mark.asyncio
async def test_single_store_guardrail_blocks_cross_store_mixing(client: AsyncClient, db_session: AsyncSession):
    """Verifies that add_to_cart in DiscoveryAgent blocks adding items from a second restaurant into the same cart."""
    # 1. Create Restaurant A (Bakery)
    m1 = Merchant(
        name="Sweet Chariot Test Bakery",
        email=f"sweet_chariot_{uuid.uuid4().hex[:6]}@test.com",
        description="Artisan cakes and pastries",
        is_active=True,
    )
    # 2. Create Restaurant B (Darshini)
    m2 = Merchant(
        name="Brahmins Coffee Bar Test",
        email=f"brahmins_{uuid.uuid4().hex[:6]}@test.com",
        description="Authentic South Indian breakfast",
        is_active=True,
    )
    db_session.add_all([m1, m2])
    await db_session.commit()
    await db_session.refresh(m1)
    await db_session.refresh(m2)

    # 3. Add products to Restaurant A
    cake = Product(
        merchant_id=m1.id,
        name="Warm Chocolate Lava Cake",
        price=175.0,
        category="Cakes",
        in_stock=True,
    )
    brownie = Product(
        merchant_id=m1.id,
        name="Walnut Fudge Brownie",
        price=120.0,
        category="Pastries",
        in_stock=True,
    )
    # 4. Add product to Restaurant B
    dosa = Product(
        merchant_id=m2.id,
        name="Ghee Roast Masala Dosa",
        price=85.0,
        category="South Indian",
        in_stock=True,
    )
    db_session.add_all([cake, brownie, dosa])
    await db_session.commit()
    await db_session.refresh(cake)
    await db_session.refresh(brownie)
    await db_session.refresh(dosa)

    # 5. Create conversation
    conv = Conversation(
        channel="web",
        merchant_id=None,
        cart={"items": [], "total": 0.0},
        messages=[],
    )
    db_session.add(conv)
    await db_session.commit()
    await db_session.refresh(conv)

    # 6. Add Item 1 from Sweet Chariot
    t_res1, act1, r_id1, r_name1, cart1, _ = await discovery_agent._execute_tool(
        db=db_session,
        conversation=conv,
        fn_name="add_to_cart",
        fn_args={"product_id": str(cake.id)},
        cart=conv.cart,
        city_merchants=[],
        recommendations=[],
        last_search_query="",
    )
    assert t_res1["success"] is True
    assert len(cart1["items"]) == 1
    assert cart1["items"][0]["name"] == "Warm Chocolate Lava Cake"
    assert cart1["items"][0]["merchant_id"] == str(m1.id)
    assert cart1["merchant_id"] == str(m1.id)
    assert conv.merchant_id == m1.id

    # 7. Attempt to add Item 2 from Brahmins Coffee Bar (cross-restaurant!)
    t_res2, act2, r_id2, r_name2, cart2, _ = await discovery_agent._execute_tool(
        db=db_session,
        conversation=conv,
        fn_name="add_to_cart",
        fn_args={"product_name": "Ghee Roast Masala Dosa", "merchant_name": "Brahmins"},
        cart=cart1,
        city_merchants=[],
        recommendations=[],
        last_search_query="",
    )

    # Verify hard guardrail triggered
    assert t_res2["success"] is False
    assert t_res2["store_mismatch"] is True
    assert t_res2["existing_store_name"] == "Sweet Chariot Test Bakery"
    assert t_res2["attempted_store_name"] == "Brahmins Coffee Bar Test"
    assert t_res2["attempted_product"] == "Ghee Roast Masala Dosa"
    assert "suggested_store_alternatives" in t_res2
    # Verify cart was NOT contaminated
    assert len(cart2["items"]) == 1
    assert cart2["items"][0]["name"] == "Warm Chocolate Lava Cake"
    assert cart2["total"] == 175.0


@pytest.mark.asyncio
async def test_store_affinity_search_prioritizes_existing_store(client: AsyncClient, db_session: AsyncSession):
    """Verifies that if a cart has Store A, adding an item also present in Store A picks Store A's version."""
    m1 = Merchant(name="Store A Coffee", email=f"a_{uuid.uuid4().hex[:6]}@test.com", is_active=True)
    m2 = Merchant(name="Store B Coffee", email=f"b_{uuid.uuid4().hex[:6]}@test.com", is_active=True)
    db_session.add_all([m1, m2])
    await db_session.commit()
    await db_session.refresh(m1)
    await db_session.refresh(m2)

    cookie = Product(merchant_id=m1.id, name="Choco Cookie", price=50.0, in_stock=True)
    coffee_a = Product(merchant_id=m1.id, name="Cold Brew Coffee", price=150.0, in_stock=True)
    coffee_b = Product(merchant_id=m2.id, name="Cold Brew Coffee", price=140.0, in_stock=True)
    db_session.add_all([cookie, coffee_a, coffee_b])
    await db_session.commit()
    await db_session.refresh(cookie)
    await db_session.refresh(coffee_a)
    await db_session.refresh(coffee_b)

    conv = Conversation(
        channel="web",
        merchant_id=None,
        cart={"items": [], "total": 0.0},
        messages=[],
    )
    db_session.add(conv)
    await db_session.commit()
    await db_session.refresh(conv)

    # Add cookie from Store A
    _, _, _, _, cart1, _ = await discovery_agent._execute_tool(
        db=db_session,
        conversation=conv,
        fn_name="add_to_cart",
        fn_args={"product_id": str(cookie.id)},
        cart=conv.cart,
        city_merchants=[],
        recommendations=[],
        last_search_query="",
    )

    # Search and add "cold brew coffee" without specifying merchant
    t_res2, _, _, _, cart2, _ = await discovery_agent._execute_tool(
        db=db_session,
        conversation=conv,
        fn_name="add_to_cart",
        fn_args={"product_name": "cold brew coffee"},
        cart=cart1,
        city_merchants=[],
        recommendations=[],
        last_search_query="",
    )

    # Must resolve to coffee_a (same store), NOT coffee_b
    assert t_res2["success"] is True
    assert len(cart2["items"]) == 2
    assert cart2["items"][1]["product_id"] == str(coffee_a.id)
    assert cart2["items"][1]["merchant_id"] == str(m1.id)


@pytest.mark.asyncio
async def test_clear_cart_tool_resets_cart_and_unlocks_store(client: AsyncClient, db_session: AsyncSession):
    """Verifies that clear_cart clears cart items, total, and unlocks conversation from merchant."""
    m1 = Merchant(name="Test Store", email=f"store_{uuid.uuid4().hex[:6]}@test.com", is_active=True)
    db_session.add(m1)
    await db_session.commit()
    await db_session.refresh(m1)

    p1 = Product(merchant_id=m1.id, name="Test Item", price=100.0, in_stock=True)
    db_session.add(p1)
    await db_session.commit()
    await db_session.refresh(p1)

    conv = Conversation(
        channel="web",
        merchant_id=m1.id,
        cart={"items": [{"product_id": str(p1.id), "name": p1.name, "price": 100.0, "quantity": 1}], "total": 100.0},
        messages=[],
    )
    db_session.add(conv)
    await db_session.commit()
    await db_session.refresh(conv)

    t_res, act, r_id, r_name, cart, _ = await discovery_agent._execute_tool(
        db=db_session,
        conversation=conv,
        fn_name="clear_cart",
        fn_args={},
        cart=conv.cart,
        city_merchants=[],
        recommendations=[],
        last_search_query="",
    )

    assert t_res["success"] is True
    assert cart["items"] == []
    assert cart["total"] == 0.0
    assert conv.merchant_id is None


@pytest.mark.asyncio
async def test_streaming_clear_cart_fastpath(client: AsyncClient, db_session: AsyncSession):
    """Verifies that saying 'clear cart' in streaming mode clears cart and unlinks store."""
    m = Merchant(name="Test FastPath Store", email=f"fastpath_{uuid.uuid4().hex[:6]}@test.com", is_active=True)
    db_session.add(m)
    await db_session.commit()
    await db_session.refresh(m)

    conv = Conversation(
        channel="web",
        merchant_id=m.id,
        cart={"items": [{"name": "Sample Cake", "price": 200.0, "quantity": 1}], "total": 200.0},
        messages=[],
    )
    db_session.add(conv)
    await db_session.commit()
    await db_session.refresh(conv)

    events = []
    async for event in discovery_agent.process_message_streaming(db_session, conv, "clear cart"):
        events.append(event)

    assert any(e.get("type") == "answer" and "cleared" in e.get("content", "").lower() for e in events)
    assert conv.cart["items"] == []
    assert conv.cart["total"] == 0.0
    assert conv.merchant_id is None


@pytest.mark.asyncio
async def test_multi_item_order_all_three_not_hijacked_as_triple_quantity(db_session: AsyncSession):
    """Verifies that 'I want to order all three from one restaurant' is NOT hijacked into 3x Option 1 cart addition."""
    m = Merchant(name="Sweet Chariot Test", email=f"sc_{uuid.uuid4().hex[:6]}@test.com", is_active=True)
    db_session.add(m)
    await db_session.commit()
    await db_session.refresh(m)

    p = Product(merchant_id=m.id, name="Warm Chocolate Lava Cake", price=175.0, in_stock=True)
    db_session.add(p)
    await db_session.commit()
    await db_session.refresh(p)

    # Simulate prior turn where recommendations were given
    conv = Conversation(
        channel="web",
        cart={"items": [], "total": 0.0},
        messages=[
            {"role": "user", "content": "I want to order one cake and one benidosa with a filter coffee may budget is 300 rupees"},
            {
                "role": "assistant",
                "content": "Here are recommendations...",
                "metadata": {
                    "recommendations": [
                        {"product_id": str(p.id), "name": p.name, "price": p.price, "merchant_id": str(m.id), "merchant_name": m.name}
                    ]
                }
            }
        ],
    )
    db_session.add(conv)
    await db_session.commit()
    await db_session.refresh(conv)

    # User replies: "I want to order all three from one restaurant"
    events = []
    async for event in discovery_agent.process_message_streaming(db_session, conv, "I want to order all three from one restaurant"):
        events.append(event)

    # MUST NOT have added 3x Warm Chocolate Lava Cake for ₹525
    cart_total = float(conv.cart.get("total", 0.0))
    items = conv.cart.get("items", [])
    assert cart_total != 525.0
    assert not any(i.get("quantity") == 3 for i in items)


@pytest.mark.asyncio
async def test_budget_guardrail_blocks_overbudget_fastpath_cart_add(db_session: AsyncSession):
    """Verifies that Fast-Path 3 blocks adding items that exceed the customer's stated budget."""
    m = Merchant(name="Sweet Chariot Test", email=f"sc_budget_{uuid.uuid4().hex[:6]}@test.com", is_active=True)
    db_session.add(m)
    await db_session.commit()
    await db_session.refresh(m)

    p = Product(merchant_id=m.id, name="Warm Chocolate Lava Cake", price=175.0, in_stock=True)
    db_session.add(p)
    await db_session.commit()
    await db_session.refresh(p)

    # Stated budget of ₹300
    conv = Conversation(
        channel="web",
        cart={"items": [], "total": 0.0},
        messages=[
            {"role": "user", "content": "My budget is 300 rupees"},
            {
                "role": "assistant",
                "content": "Here are recommendations...",
                "metadata": {
                    "recommendations": [
                        {"product_id": str(p.id), "name": p.name, "price": p.price, "merchant_id": str(m.id), "merchant_name": m.name}
                    ]
                }
            }
        ],
    )
    db_session.add(conv)
    await db_session.commit()
    await db_session.refresh(conv)

    # User asks to add 2x lava cake = 2 * 175 = ₹350 (exceeds budget 300)
    events = []
    async for event in discovery_agent.process_message_streaming(db_session, conv, "add 2x option 1 to cart"):
        events.append(event)

    # Must be blocked by Budget Guardrail
    answer_event = next((e for e in events if e.get("type") == "answer"), None)
    assert answer_event is not None
    assert "Budget Guardrail" in answer_event.get("content", "")
    assert conv.cart.get("total", 0.0) == 0.0  # Cart was not mutated


@pytest.mark.asyncio
async def test_conversational_clarification_no_shop_which_serves_both(db_session: AsyncSession):
    """Verifies that asking 'so there is no shop which serves both ?' receives an intelligent answer, not fallback template."""
    conv = Conversation(
        channel="web",
        cart={"items": [], "total": 0.0},
        messages=[
            {"role": "user", "content": "order one filter coffee one pizza"},
            {
                "role": "assistant",
                "content": "Each delivery order must come from a single restaurant kitchen, so we can't mix a filter coffee and a pizza in the same cart.",
            }
        ],
    )
    db_session.add(conv)
    await db_session.commit()
    await db_session.refresh(conv)

    events = []
    async for event in discovery_agent.process_message_streaming(db_session, conv, "so there is no shop which serves both ?"):
        events.append(event)

    answer_event = next((e for e in events if e.get("type") == "answer"), None)
    assert answer_event is not None
    content = answer_event.get("content", "")

    # Must NOT be the robotic fallback template
    assert "I've discovered these options across Bangalore stores for you. Which store would you like to explore?" not in content

    # Recommendations must be 0 for purely conversational question
    chat_resp = answer_event.get("chat_response", {})
    recs = chat_resp.get("recommendations") or []
    assert len(recs) == 0


@pytest.mark.asyncio
async def test_multi_item_balanced_recommendations_coffee_and_pizza(db_session: AsyncSession):
    """Verifies that multi-item requests with typos like 'filetrr coffee' and 'pizza' yield balanced cards."""
    conv = Conversation(
        channel="web",
        cart={"items": [], "total": 0.0},
        messages=[],
    )
    db_session.add(conv)
    await db_session.commit()
    await db_session.refresh(conv)

    events = []
    async for event in discovery_agent.process_message_streaming(db_session, conv, "order one filetrr coffee one pizza"):
        events.append(event)

    answer_event = next((e for e in events if e.get("type") == "answer"), None)
    assert answer_event is not None
    content = answer_event.get("content", "")

    # Must explain single-store constraint
    assert "single" in content.lower() or "kitchen" in content.lower() or "separate" in content.lower()

    chat_resp = answer_event.get("chat_response", {})
    recs = chat_resp.get("recommendations") or []
    assert len(recs) <= 4

    # If cards are populated, must contain authentic filter coffee, not just cold brews
    if recs:
        card_names = [r.get("name", "").lower() for r in recs]
        has_filter_coffee = any("filter coffee" in n for n in card_names)
        assert has_filter_coffee, f"Expected filter coffee in recommendations, got: {card_names}"


