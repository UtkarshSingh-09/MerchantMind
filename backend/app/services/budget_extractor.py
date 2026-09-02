"""Structured Budget Extraction Service using Groq LLM.
Extracts budget constraints, currency, and strictness from conversational intent.
"""

import json
import logging
from typing import Any
from app.services.groq_client import groq_client

logger = logging.getLogger(__name__)

EXTRACTION_SYSTEM_PROMPT = """You are a financial constraint extraction model for an e-commerce shopping agent.
Analyze the user's messages and extract any stated budget or spending constraints.

Return ONLY a valid JSON object matching this exact schema:
{
  "budget_amount": number or null,
  "currency": "INR",
  "is_hard_limit": boolean,
  "raw_phrase": string or null,
  "reasoning": string
}

Rules:
1. If the user specifies a maximum, strict budget ("under 700", "max 500", "not more than 1000", "within 800 rs"), set `budget_amount` to that number and `is_hard_limit` to true.
2. If the user mentions an approximate or soft budget ("around 600ish", "approx 500", "about 700"), set `budget_amount` to that number and `is_hard_limit` to false.
3. If no budget is mentioned, return `"budget_amount": null, "is_hard_limit": false, "raw_phrase": null, "reasoning": "No budget constraint mentioned."`.
4. Output raw JSON only. Do not enclose in markdown blocks or backticks.
"""


async def extract_structured_budget(messages: list[dict[str, Any]]) -> dict[str, Any]:
    """Extract structured budget info from recent user messages."""
    # Filter to user messages only to prevent assistant hallucinations
    user_msgs = [m for m in messages if m.get("role") == "user"]
    if not user_msgs:
        return {
            "budget_amount": None,
            "currency": "INR",
            "is_hard_limit": False,
            "raw_phrase": None,
            "reasoning": "No user message provided",
        }

    # Extract from last 4 user messages
    recent_context = "\n".join([f"User: {m.get('content', '')}" for m in user_msgs[-4:]])

    try:
        response = await groq_client.fast_completion(
            messages=[
                {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
                {"role": "user", "content": f"Extract budget from these customer messages:\n{recent_context}"},
            ],
            temperature=0.0,
            max_tokens=400,
            response_format={"type": "json_object"},
        )
        content = (response.choices[0].message.content or "").strip()
        # Clean JSON if backticks present
        if content.startswith("```"):
            content = content.strip("`").removeprefix("json").strip()

        data = json.loads(content)
        amount = data.get("budget_amount")
        if amount is not None:
            try:
                data["budget_amount"] = float(amount)
            except (ValueError, TypeError):
                data["budget_amount"] = None

        return {
            "budget_amount": data.get("budget_amount"),
            "currency": data.get("currency", "INR"),
            "is_hard_limit": bool(data.get("is_hard_limit", False)),
            "raw_phrase": data.get("raw_phrase"),
            "reasoning": data.get("reasoning", ""),
        }
    except Exception as exc:
        logger.warning("Structured budget extraction fallback: %s", exc)
        return {
            "budget_amount": None,
            "currency": "INR",
            "is_hard_limit": False,
            "raw_phrase": None,
            "reasoning": f"Extraction error: {str(exc)}",
        }
