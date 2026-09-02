"""Comprehensive fuzzing and edge case test suite for EntityResolver."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.entity_resolver import entity_resolver, calculate_similarity


@pytest.fixture
def mock_catalog():
    return [
        {"id": "prod_1", "name": "Belgian Chocolate Truffle Cake", "price": 850.0, "category": "Cakes"},
        {"id": "prod_2", "name": "Red Velvet Pastry", "price": 180.0, "category": "Pastries"},
        {"id": "prod_3", "name": "Artisan Sourdough Bread", "price": 220.0, "category": "Bread"},
        {"id": "prod_4", "name": "Cold Brew Coffee", "price": 160.0, "category": "Beverages"},
        {"id": "prod_5", "name": "Chocolate Croissant", "price": 140.0, "category": "Pastries"},
    ]


def test_similarity_exact_match():
    """Identical strings have 1.0 similarity score."""
    assert calculate_similarity("Red Velvet Pastry", "Red Velvet Pastry") == 1.0


def test_similarity_substring_match():
    """Substring matching yields high confidence."""
    assert calculate_similarity("sourdough", "Artisan Sourdough Bread") >= 0.90


def test_similarity_typo_fuzzy_match():
    """Fuzzy matching handles misspellings."""
    score = calculate_similarity("choclate trufle", "Belgian Chocolate Truffle Cake")
    assert score > 0.45


def test_similarity_case_insensitivity():
    """Case variations produce identical similarity scores."""
    score1 = calculate_similarity("cold brew", "Cold Brew Coffee")
    score2 = calculate_similarity("COLD BREW", "cold brew coffee")
    assert score1 == score2 >= 0.85


def test_similarity_punctuation_stripping():
    """Special characters and punctuation do not reduce similarity."""
    score = calculate_similarity("Chocolate Cake!!!", "Chocolate Cake")
    assert score == 1.0


@pytest.mark.asyncio
async def test_resolve_cart_edits_add_action(mock_catalog):
    """Resolves add intent to catalog item."""
    mock_resp = MagicMock()
    mock_resp.choices = [
        MagicMock(message=MagicMock(content='{"intent_type": "cart_edit", "actions": [{"action": "add", "item_phrase": "Cold Brew Coffee", "quantity": 2}]}'))
    ]
    with patch("app.services.groq_client.groq_client.fast_completion", new_callable=AsyncMock, return_value=mock_resp):
        res = await entity_resolver.parse_and_resolve_cart_edits(
            user_message="Add 2 cold brews",
            cart_items=[],
            available_products=mock_catalog,
        )
        assert res["is_cart_edit"] is True
        assert len(res["actions"]) == 1
        assert res["actions"][0]["product_id"] == "prod_4"
        assert res["actions"][0]["quantity"] == 2


@pytest.mark.asyncio
async def test_resolve_cart_edits_remove_action():
    """Resolves remove intent to existing cart item."""
    cart = [{"product_id": "prod_1", "name": "Belgian Chocolate Truffle Cake", "price": 850.0, "quantity": 1}]
    mock_resp = MagicMock()
    mock_resp.choices = [
        MagicMock(message=MagicMock(content='{"intent_type": "cart_edit", "actions": [{"action": "remove", "item_phrase": "chocolate cake", "quantity": 1}]}'))
    ]
    with patch("app.services.groq_client.groq_client.fast_completion", new_callable=AsyncMock, return_value=mock_resp):
        res = await entity_resolver.parse_and_resolve_cart_edits(
            user_message="Remove the chocolate cake",
            cart_items=cart,
            available_products=[],
        )
        assert res["is_cart_edit"] is True
        assert len(res["actions"]) == 1
        assert res["actions"][0]["action"] == "remove"
        assert res["actions"][0]["product_id"] == "prod_1"


@pytest.mark.asyncio
async def test_resolve_cart_edits_clear_action():
    """Clear action resets cart."""
    mock_resp = MagicMock()
    mock_resp.choices = [
        MagicMock(message=MagicMock(content='{"intent_type": "cart_edit", "actions": [{"action": "clear"}]}'))
    ]
    with patch("app.services.groq_client.groq_client.fast_completion", new_callable=AsyncMock, return_value=mock_resp):
        res = await entity_resolver.parse_and_resolve_cart_edits(
            user_message="Clear my cart",
            cart_items=[],
            available_products=[],
        )
        assert res["is_cart_edit"] is True
        assert res["actions"][0]["action"] == "clear"


@pytest.mark.asyncio
async def test_resolve_non_cart_query_returns_false():
    """Standard inquiry message returns is_cart_edit False."""
    mock_resp = MagicMock()
    mock_resp.choices = [
        MagicMock(message=MagicMock(content='{"intent_type": "query", "actions": []}'))
    ]
    with patch("app.services.groq_client.groq_client.fast_completion", new_callable=AsyncMock, return_value=mock_resp):
        res = await entity_resolver.parse_and_resolve_cart_edits(
            user_message="What time do you close?",
            cart_items=[],
            available_products=[],
        )
        assert res["is_cart_edit"] is False
        assert len(res["actions"]) == 0


@pytest.mark.asyncio
async def test_resolve_ambiguous_cart_items_generates_clarification():
    """Ambiguous remove intent with multiple close matches generates clarification prompt."""
    cart = [
        {"product_id": "prod_1", "name": "Dark Chocolate Truffle Cake", "price": 850.0, "quantity": 1},
        {"product_id": "prod_2", "name": "Milk Chocolate Truffle Cake", "price": 850.0, "quantity": 1},
    ]
    mock_resp = MagicMock()
    mock_resp.choices = [
        MagicMock(message=MagicMock(content='{"intent_type": "cart_edit", "actions": [{"action": "remove", "item_phrase": "chocolate cake", "quantity": 1}]}'))
    ]
    with patch("app.services.groq_client.groq_client.fast_completion", new_callable=AsyncMock, return_value=mock_resp):
        res = await entity_resolver.parse_and_resolve_cart_edits(
            user_message="Remove the chocolate cake",
            cart_items=cart,
            available_products=[],
        )
        assert len(res["clarifications"]) > 0
        assert "Which one" in res["clarifications"][0] or "both" in res["clarifications"][0]
