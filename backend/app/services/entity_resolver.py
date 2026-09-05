"""Deterministic Entity Resolution & Multi-Item Intent Resolver.
Handles free-form conversational cart instructions (e.g. 'remove that cake and add 2 coffees'),
fuzzy string token matching against catalog/cart items, confidence scoring,
and 1-turn clarification generation when ambiguous.
"""

import json
import logging
import re
from typing import Any
from difflib import SequenceMatcher
from app.services.groq_client import groq_client

logger = logging.getLogger(__name__)


def calculate_similarity(a: str, b: str) -> float:
    """Calculate token-aware similarity score between two item descriptions (0.0 to 1.0)."""
    norm_a = re.sub(r"[^\w\s]", "", a.lower()).strip()
    norm_b = re.sub(r"[^\w\s]", "", b.lower()).strip()

    if norm_a == norm_b:
        return 1.0

    # Substring match
    if norm_a in norm_b or norm_b in norm_a:
        return 0.90

    # Sequence matcher on full text
    seq_ratio = SequenceMatcher(None, norm_a, norm_b).ratio()

    # Token overlap score
    tokens_a = set(norm_a.split())
    tokens_b = set(norm_b.split())
    if tokens_a and tokens_b:
        overlap = len(tokens_a.intersection(tokens_b)) / max(len(tokens_a), len(tokens_b))
    else:
        overlap = 0.0

    return max(seq_ratio, overlap)


EXTRACTION_PROMPT = """You are a precise e-commerce cart instruction parser.
Analyze the user's message and determine all intended cart modification actions.

Available actions: "add", "remove", "update_qty", "clear", "none".

Return a valid JSON object matching this schema:
{
  "intent_type": "cart_edit" | "query" | "checkout",
  "actions": [
    {
      "action": "add" | "remove" | "update_qty" | "clear",
      "item_phrase": "name or description of the item",
      "quantity": integer (default 1)
    }
  ],
  "overall_confidence": float between 0.0 and 1.0,
  "ambiguity_detected": boolean
}

Examples:
- "Remove the pav bhaji and add 2 chole bhature" ->
  {"intent_type": "cart_edit", "actions": [{"action": "remove", "item_phrase": "pav bhaji", "quantity": 1}, {"action": "add", "item_phrase": "chole bhature", "quantity": 2}], "overall_confidence": 0.98, "ambiguity_detected": false}
- "Drop that cake" ->
  {"intent_type": "cart_edit", "actions": [{"action": "remove", "item_phrase": "cake", "quantity": 1}], "overall_confidence": 0.90, "ambiguity_detected": false}
"""


class EntityResolver:
    """Service to parse compound cart modifications and resolve them to exact database items."""

    async def parse_and_resolve_cart_edits(
        self,
        user_message: str,
        cart_items: list[dict[str, Any]] | None = None,
        available_products: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Parse freeform cart modifications and match them deterministically against cart/catalog items."""
        cart_items = cart_items or []
        available_products = available_products or []
        # 1. Fast LLM Parse using Fast Tier
        try:
            response = await groq_client.fast_completion(
                messages=[
                    {"role": "system", "content": EXTRACTION_PROMPT},
                    {"role": "user", "content": user_message},
                ],
                temperature=0.0,
                max_tokens=300,
                response_format={"type": "json_object"},
            )
            parsed = json.loads(response.choices[0].message.content or "{}")
        except Exception as exc:
            logger.warning("Fast LLM cart parse failed: %s", exc)
            return {"is_cart_edit": False, "actions": [], "clarification": None}

        if parsed.get("intent_type") != "cart_edit" or not parsed.get("actions"):
            return {"is_cart_edit": False, "actions": [], "clarification": None}

        resolved_actions = []
        clarifications = []

        for act in parsed.get("actions", []):
            action_type = act.get("action")
            phrase = act.get("item_phrase", "")
            qty = max(1, int(act.get("quantity", 1)))

            if action_type == "clear":
                resolved_actions.append({"action": "clear"})
                continue

            if action_type in ("remove", "update_qty"):
                # Match against current cart items
                best_match = None
                best_score = 0.0
                all_candidate_matches = []

                for item in cart_items:
                    score = calculate_similarity(phrase, item.get("name", ""))
                    if score > 0.45:
                        all_candidate_matches.append((item, score))
                    if score > best_score:
                        best_score = score
                        best_match = item

                # Check ambiguity
                if len(all_candidate_matches) > 1 and all_candidate_matches[0][1] - all_candidate_matches[1][1] < 0.15:
                    candidate_names = [f"'{c[0].get('name')}'" for c in all_candidate_matches[:2]]
                    clarifications.append(
                        f"You have both {' and '.join(candidate_names)} in your cart. Which one would you like to {action_type}?"
                    )
                    continue

                if best_match and best_score >= 0.50:
                    resolved_actions.append({
                        "action": action_type,
                        "product_id": best_match.get("product_id"),
                        "name": best_match.get("name"),
                        "quantity": qty,
                        "unit_price": best_match.get("unit_price") or best_match.get("price", 0),
                        "confidence": best_score,
                    })
                else:
                    clarifications.append(f"I couldn't find '{phrase}' in your cart to {action_type}.")

            elif action_type == "add":
                # Match against available merchant products
                best_prod = None
                best_score = 0.0

                for prod in available_products:
                    score = calculate_similarity(phrase, prod.get("name", ""))
                    if score > best_score:
                        best_score = score
                        best_prod = prod

                if best_prod and best_score >= 0.55:
                    resolved_actions.append({
                        "action": "add",
                        "product_id": best_prod.get("id") or best_prod.get("product_id"),
                        "name": best_prod.get("name"),
                        "quantity": qty,
                        "unit_price": best_prod.get("price", 0),
                        "confidence": best_score,
                    })
                else:
                    # Low confidence — let normal agent search process it
                    return {"is_cart_edit": False, "actions": [], "clarification": None}

        return {
            "is_cart_edit": len(resolved_actions) > 0 or len(clarifications) > 0,
            "actions": resolved_actions,
            "clarifications": clarifications,
        }

    def resolve_product_fuzzy(
        self, query: str, available_products: list[dict[str, Any]]
    ) -> dict[str, Any] | None:
        """Find the best-matching product from a list using token-aware similarity scoring."""
        best_prod = None
        best_score = 0.0
        for p in available_products:
            score = calculate_similarity(query, p.get("name", ""))
            if score > best_score:
                best_score = score
                best_prod = p
        return best_prod if best_score >= 0.40 else None


entity_resolver = EntityResolver()

