"""Comprehensive test suite for Structured Budget Extractor."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.budget_extractor import extract_structured_budget


@pytest.mark.asyncio
async def test_extract_hard_budget_limit():
    """Validates strict upper limit detection ('under 500 max')."""
    messages = [{"role": "user", "content": "I want a chocolate cake under 500 max"}]
    mock_resp = MagicMock()
    mock_resp.choices = [
        MagicMock(message=MagicMock(content='{"budget_amount": 500, "currency": "INR", "is_hard_limit": true, "raw_phrase": "under 500 max", "reasoning": "Explicit max limit"}'))
    ]
    with patch("app.services.groq_client.groq_client.fast_completion", new_callable=AsyncMock, return_value=mock_resp):
        res = await extract_structured_budget(messages)
        assert res["budget_amount"] == 500.0
        assert res["is_hard_limit"] is True
        assert res["currency"] == "INR"


@pytest.mark.asyncio
async def test_extract_soft_budget_limit():
    """Validates approximate budget detection ('around 1200')."""
    messages = [{"role": "user", "content": "Looking for snacks, budget is around 1200 or so"}]
    mock_resp = MagicMock()
    mock_resp.choices = [
        MagicMock(message=MagicMock(content='{"budget_amount": 1200, "currency": "INR", "is_hard_limit": false, "raw_phrase": "around 1200", "reasoning": "Soft approximate budget"}'))
    ]
    with patch("app.services.groq_client.groq_client.fast_completion", new_callable=AsyncMock, return_value=mock_resp):
        res = await extract_structured_budget(messages)
        assert res["budget_amount"] == 1200.0
        assert res["is_hard_limit"] is False


@pytest.mark.asyncio
async def test_extract_no_budget_mentioned():
    """Returns None when user does not mention spending limits."""
    messages = [{"role": "user", "content": "Show me your pastry menu please"}]
    mock_resp = MagicMock()
    mock_resp.choices = [
        MagicMock(message=MagicMock(content='{"budget_amount": null, "currency": "INR", "is_hard_limit": false, "raw_phrase": null, "reasoning": "No budget mentioned"}'))
    ]
    with patch("app.services.groq_client.groq_client.fast_completion", new_callable=AsyncMock, return_value=mock_resp):
        res = await extract_structured_budget(messages)
        assert res["budget_amount"] is None
        assert res["is_hard_limit"] is False


@pytest.mark.asyncio
async def test_extract_empty_messages():
    """Empty message history gracefully returns null budget without calling LLM."""
    res = await extract_structured_budget([])
    assert res["budget_amount"] is None
    assert res["is_hard_limit"] is False


@pytest.mark.asyncio
async def test_extract_assistant_only_messages():
    """Messages with no user role return null budget."""
    messages = [{"role": "assistant", "content": "Your total is Rs 500"}]
    res = await extract_structured_budget(messages)
    assert res["budget_amount"] is None


@pytest.mark.asyncio
async def test_extract_malformed_json_fallback():
    """Malformed LLM response falls back to null budget safely."""
    messages = [{"role": "user", "content": "Budget is 400 rs"}]
    mock_resp = MagicMock()
    mock_resp.choices = [MagicMock(message=MagicMock(content="INVALID JSON STRING"))]
    with patch("app.services.groq_client.groq_client.fast_completion", new_callable=AsyncMock, return_value=mock_resp):
        res = await extract_structured_budget(messages)
        assert res["budget_amount"] is None


@pytest.mark.asyncio
async def test_extract_markdown_fenced_json():
    """Parses JSON wrapped in markdown code blocks."""
    messages = [{"role": "user", "content": "keep it under 800"}]
    mock_resp = MagicMock()
    mock_resp.choices = [
        MagicMock(message=MagicMock(content='```json\n{"budget_amount": 800, "currency": "INR", "is_hard_limit": true, "raw_phrase": "under 800", "reasoning": "Strict"}\n```'))
    ]
    with patch("app.services.groq_client.groq_client.fast_completion", new_callable=AsyncMock, return_value=mock_resp):
        res = await extract_structured_budget(messages)
        assert res["budget_amount"] == 800.0
        assert res["is_hard_limit"] is True


@pytest.mark.asyncio
async def test_extract_numeric_type_conversion():
    """Converts string numbers ('650.50') into float numbers."""
    messages = [{"role": "user", "content": "650.50 max"}]
    mock_resp = MagicMock()
    mock_resp.choices = [
        MagicMock(message=MagicMock(content='{"budget_amount": "650.50", "currency": "INR", "is_hard_limit": true, "raw_phrase": "650.50 max", "reasoning": "Float string"}'))
    ]
    with patch("app.services.groq_client.groq_client.fast_completion", new_callable=AsyncMock, return_value=mock_resp):
        res = await extract_structured_budget(messages)
        assert res["budget_amount"] == 650.50
