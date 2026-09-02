"""Conversation Memory Optimization Service.
Provides sliding window context management and LLM-powered summarization
for long-running multi-turn shopping and discovery conversations.
"""

import json
import logging
from typing import Any
from app.models.conversation import Conversation
from app.services.groq_client import groq_client

logger = logging.getLogger(__name__)

SUMMARIZATION_SYSTEM_PROMPT = """You are a conversation memory compression engine for an AI e-commerce agent.
Your task is to summarize past messages concisely without losing vital shopping context.

Key elements to retain:
1. Customer's explicit needs, preferences, dietary constraints, occasions (e.g. birthday, anniversary).
2. Budget constraints mentioned (amount, flexible vs hard).
3. Products discussed, accepted, or rejected.
4. Stores mentioned or visited.
5. Delivery / Pickup preferences.

Output format: A concise 2-4 sentence summary bulleted context. Do NOT include greetings or fluff.
"""


async def summarize_older_messages(messages: list[dict[str, Any]]) -> str:
    """Compress older conversation turns into a dense factual summary."""
    if not messages:
        return ""

    transcript_lines = []
    for m in messages:
        role = m.get("role", "user")
        content = m.get("content", "")
        if content and role in ("user", "assistant"):
            transcript_lines.append(f"{role.upper()}: {content}")

    if not transcript_lines:
        return ""

    transcript_text = "\n".join(transcript_lines)

    try:
        response = await groq_client.fast_completion(
            messages=[
                {"role": "system", "content": SUMMARIZATION_SYSTEM_PROMPT},
                {"role": "user", "content": f"Summarize this conversation history:\n{transcript_text}"},
            ],
            temperature=0.0,
            max_tokens=220,
        )
        summary = (response.choices[0].message.content or "").strip()
        return summary
    except Exception as exc:
        logger.warning("Memory summarization failed, falling back to truncated transcript: %s", exc)
        # Fallback: simple text truncation of the latest items in older turns
        return f"Previous turns covered: {transcript_lines[-3:]}"


async def build_optimized_context(
    conversation: Conversation,
    max_recent: int = 6,
) -> list[dict[str, Any]]:
    """Build a context-window optimized message list for LLM prompting.

    - If history <= max_recent + 2: returns full message history.
    - If history > max_recent + 2: summarizes older turns and attaches recent verbatim turns.
    """
    raw_messages = list(conversation.messages or [])

    # Filter only valid user/assistant turns
    valid_turns = [
        m for m in raw_messages
        if m.get("role") in ("user", "assistant") and m.get("content")
    ]

    if len(valid_turns) <= max_recent + 2:
        return [
            {"role": m.get("role"), "content": m.get("content")}
            for m in valid_turns
        ]

    # Split into older and recent
    older_turns = valid_turns[:-max_recent]
    recent_turns = valid_turns[-max_recent:]

    summary_text = await summarize_older_messages(older_turns)

    optimized: list[dict[str, Any]] = []

    if summary_text:
        optimized.append({
            "role": "system",
            "content": f"📋 PREVIOUS CONVERSATION CONTEXT (Summarized from earlier turns):\n{summary_text}",
        })

    for m in recent_turns:
        optimized.append({
            "role": m.get("role"),
            "content": m.get("content"),
        })

    return optimized
