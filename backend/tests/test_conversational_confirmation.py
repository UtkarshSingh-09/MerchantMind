import pytest
import uuid
from app.models.conversation import Conversation
from app.models.customer import Customer
from app.models.merchant import Merchant
from app.models.product import Product
from app.agents.discovery_agent import DiscoveryAgent


@pytest.mark.asyncio
async def test_affirmative_yes_adds_recommended_coffee_to_cart(db_session):
    """
    Verify that when assistant recommends an item (e.g. Filter Coffee from Taaza Thindi)
    and asks 'Shall I add 1 x Filter Coffee... Just say yes', saying 'yes'
    adds the item to the cart instead of erroneously triggering an empty cart checkout message.
    """
    # 1. Setup Merchant and Customer
    merchant_id = uuid.uuid4()
    merchant = Merchant(
        id=merchant_id,
        name="Taaza Thindi",
        email=f"taaza_{merchant_id.hex[:6]}@example.com",
        cuisine_type="South Indian",
        avg_rating=4.8,
        is_active=True,
    )
    db_session.add(merchant)
    await db_session.flush()

    customer_id = uuid.uuid4()
    customer = Customer(
        id=customer_id,
        merchant_id=merchant_id,
        name="Utkarsh",
        phone="+919876543210",
    )
    db_session.add(customer)
    await db_session.flush()

    product_id = uuid.uuid4()
    product = Product(
        id=product_id,
        merchant_id=merchant.id,
        name="Filter Coffee (Degree Coffee)",
        price=25.0,
        in_stock=True,
        rating=4.8,
        category="Beverages",
    )
    db_session.add(product)
    await db_session.commit()

    agent = DiscoveryAgent()

    # 2. Setup Conversation with previous turns matching user transcript
    conversation = Conversation(
        id=uuid.uuid4(),
        customer_id=customer_id,
        cart={"items": [], "total": 0.0},
        messages=[
            {"role": "user", "content": "add one cifee"},
            {
                "role": "assistant",
                "content": "Great choice! Let’s start with the filter coffee first. Here are the top-rated options...",
                "metadata": {
                    "recommendations": [
                        {
                            "id": str(product.id),
                            "product_id": str(product.id),
                            "name": product.name,
                            "price": product.price,
                            "merchant_name": merchant.name,
                            "merchant_id": str(merchant.id),
                            "rating": 4.8,
                        }
                    ]
                },
            },
            {"role": "user", "content": "anyone i am new i dont know much"},
            {
                "role": "assistant",
                "content": (
                    "No worries at all, Utkarsh! Let me make this super easy for you. 🙌 "
                    "Since you’re new, I’d recommend Option 1: Taaza Thindi, Banashankari — it’s the highest-rated (4.8 ⭐) "
                    "and serves that classic, strong Degree Filter Coffee that’s a Bangalore institution. It’s just ₹25, so it’s a no-brainer! "
                    "Shall I add 1 × Filter Coffee from Taaza Thindi to your cart? Just say “yes” and I’ll do it right away! ☕"
                ),
            },
        ],
    )
    db_session.add(conversation)
    await db_session.commit()

    # 3. User says "yes"
    events = []
    async for ev in agent.process_message_streaming(db_session, conversation, "yes"):
        events.append(ev)

    answer_ev = next((e for e in events if e.get("type") == "answer"), None)
    assert answer_ev is not None
    chat_resp = answer_ev.get("chat_response")
    assert chat_resp is not None

    # Verify the response does NOT say "cart is currently empty"
    msg = chat_resp.get("message", "")
    assert "Your cart is currently empty" not in msg

    # Verify the item WAS added to the cart
    cart_items = conversation.cart.get("items", [])
    assert len(cart_items) == 1
    assert "Filter Coffee" in cart_items[0]["name"]
    assert cart_items[0]["price"] == 25.0
    assert conversation.cart.get("total") == 25.0

    # Verify assistant confirmed Taaza Thindi and mentioned price
    assert "Taaza Thindi" in msg
    assert "25" in msg


@pytest.mark.asyncio
async def test_delegate_choice_anyone_adds_top_rated(db_session):
    """
    Verify that when recommendations are active, saying 'anyone i am new i dont know much'
    picks the highest rated item from recommendations.
    """
    merchant_id = uuid.uuid4()
    merchant = Merchant(
        id=merchant_id,
        name="Taaza Thindi",
        email=f"taaza2_{merchant_id.hex[:6]}@example.com",
        cuisine_type="South Indian",
        avg_rating=4.8,
        is_active=True,
    )
    db_session.add(merchant)
    await db_session.flush()

    customer_id = uuid.uuid4()
    customer = Customer(
        id=customer_id,
        merchant_id=merchant_id,
        name="Utkarsh",
        phone="+919876543211",
    )
    db_session.add(customer)
    await db_session.flush()

    product_id = uuid.uuid4()
    product = Product(
        id=product_id,
        merchant_id=merchant.id,
        name="Filter Coffee (Degree Coffee)",
        price=25.0,
        in_stock=True,
        rating=4.8,
        category="Beverages",
    )
    db_session.add(product)
    await db_session.commit()

    agent = DiscoveryAgent()

    conversation = Conversation(
        id=uuid.uuid4(),
        customer_id=customer_id,
        cart={"items": [], "total": 0.0},
        messages=[
            {"role": "user", "content": "add one cifee"},
            {
                "role": "assistant",
                "content": "Here are options...",
                "metadata": {
                    "recommendations": [
                        {
                            "id": str(product.id),
                            "product_id": str(product.id),
                            "name": product.name,
                            "price": product.price,
                            "merchant_name": merchant.name,
                            "merchant_id": str(merchant.id),
                            "rating": 4.8,
                        }
                    ]
                },
            },
        ],
    )
    db_session.add(conversation)
    await db_session.commit()

    events = []
    async for ev in agent.process_message_streaming(db_session, conversation, "anyone i am new i dont know much"):
        events.append(ev)

    answer_ev = next((e for e in events if e.get("type") == "answer"), None)
    assert answer_ev is not None
    chat_resp = answer_ev.get("chat_response")
    assert chat_resp is not None

    cart_items = conversation.cart.get("items", [])
    assert len(cart_items) == 1
    assert "Filter Coffee" in cart_items[0]["name"]
    assert cart_items[0]["price"] == 25.0


@pytest.mark.asyncio
async def test_checkout_orders_in_card_triggers_pickup_delivery_and_preserves_cart(db_session):
    """
    Verify that when customer has items in cart and says:
    'check out the orders what is already at in my card' or 'please check it out',
    the assistant initiates the pickup vs delivery confirmation flow and does NOT empty the cart.
    """
    merchant_id = uuid.uuid4()
    merchant = Merchant(
        id=merchant_id,
        name="Taaza Thindi",
        email=f"taaza3_{merchant_id.hex[:6]}@example.com",
        cuisine_type="South Indian",
        avg_rating=4.8,
        is_active=True,
    )
    db_session.add(merchant)
    await db_session.flush()

    customer_id = uuid.uuid4()
    customer = Customer(
        id=customer_id,
        merchant_id=merchant_id,
        name="Utkarsh",
        phone="+919876543212",
    )
    db_session.add(customer)
    await db_session.flush()

    product_id = uuid.uuid4()
    product = Product(
        id=product_id,
        merchant_id=merchant.id,
        name="Filter Coffee (Degree Coffee)",
        price=25.0,
        in_stock=True,
        rating=4.8,
        category="Beverages",
    )
    db_session.add(product)
    await db_session.commit()

    agent = DiscoveryAgent()

    # Pre-populate cart with items
    cart_data = {
        "items": [
            {
                "product_id": str(product.id),
                "name": product.name,
                "price": product.price,
                "quantity": 1,
                "merchant_id": str(merchant.id),
                "merchant_name": merchant.name,
            }
        ],
        "total": 25.0,
        "merchant_id": str(merchant.id),
        "merchant_name": merchant.name,
    }

    conversation = Conversation(
        id=uuid.uuid4(),
        customer_id=customer_id,
        cart=cart_data,
        messages=[
            {"role": "user", "content": "add one coffee"},
            {"role": "assistant", "content": "Added 1x Filter Coffee to your cart!"},
        ],
    )
    db_session.add(conversation)
    await db_session.commit()

    # User says: "check out the orders what is already at in my card"
    events = []
    async for ev in agent.process_message_streaming(
        db_session, conversation, "check out the orders what is already at in my card"
    ):
        events.append(ev)

    answer_ev = next((e for e in events if e.get("type") == "answer"), None)
    assert answer_ev is not None
    chat_resp = answer_ev.get("chat_response")
    assert chat_resp is not None

    msg = chat_resp.get("message", "")
    # Should NOT be empty cart error
    assert "Your cart is currently empty" not in msg
    # Should ask for store pickup or doorstep delivery
    assert "pickup" in msg.lower() or "delivery" in msg.lower()
    # Cart in conversation should still have items!
    assert len(conversation.cart.get("items", [])) == 1
    assert conversation.cart.get("total") == 25.0
    # Cart in chat response should NOT be empty []
    assert chat_resp.get("cart") is not None
    assert len(chat_resp.get("cart")) == 1

    # Now test "please check it out" on same conversation
    events2 = []
    async for ev in agent.process_message_streaming(
        db_session, conversation, "please check it out"
    ):
        events2.append(ev)

    answer_ev2 = next((e for e in events2 if e.get("type") == "answer"), None)
    assert answer_ev2 is not None
    chat_resp2 = answer_ev2.get("chat_response")
    assert "Your cart is currently empty" not in chat_resp2.get("message", "")
    assert len(conversation.cart.get("items", [])) == 1


@pytest.mark.asyncio
async def test_voice_payment_command_launches_razorpay_for_active_order(db_session):
    """
    Verify that when an order is created and waiting for payment,
    a speech-to-text voice command like 'to a payment for me'
    immediately triggers the Razorpay Checkout action and payment link
    instead of refusing or saying 'I am unable to process payment on your behalf'.
    """
    from app.models.order import Order, OrderStatus
    merchant_id = uuid.uuid4()
    merchant = Merchant(
        id=merchant_id,
        name="Truffles Burgers",
        email=f"truffles_{merchant_id.hex[:6]}@example.com",
        cuisine_type="Continental",
        avg_rating=4.9,
        is_active=True,
    )
    db_session.add(merchant)
    await db_session.flush()

    conv_id = uuid.uuid4()
    conversation = Conversation(
        id=conv_id,
        cart={"items": [], "total": 0.0},
        messages=[
            {"role": "user", "content": "yeah I am saying that home address only"},
            {"role": "assistant", "content": "Your order is ready for payment! Total: ₹440"},
        ],
    )
    db_session.add(conversation)
    await db_session.flush()

    order = Order(
        id=uuid.uuid4(),
        merchant_id=merchant_id,
        conversation_id=conv_id,
        status=OrderStatus.PAYMENT_LINK_SENT,
        subtotal=440.0,
        total=440.0,
        payment_link="https://rzp.io/i/mock_plink_440",
        fulfillment_mode="delivery",
        delivery_address="Flat 402, 100 Feet Road, Indiranagar, Bangalore",
    )
    db_session.add(order)
    await db_session.commit()

    agent = DiscoveryAgent()

    # User speaks: "to a payment for me" (speech-to-text transcript)
    events = []
    async for ev in agent.process_message_streaming(db_session, conversation, "to a payment for me"):
        events.append(ev)

    answer_ev = next((e for e in events if e.get("type") == "answer"), None)
    assert answer_ev is not None
    chat_resp = answer_ev.get("chat_response")
    assert chat_resp is not None
    assert chat_resp.get("action") == "checkout"
    assert chat_resp.get("payment_link") == "https://rzp.io/i/mock_plink_440"
    assert chat_resp.get("order_id") == str(order.id)
    assert "unable to process" not in chat_resp.get("message", "").lower()
    assert "opening secure razorpay checkout" in chat_resp.get("message", "").lower()


