"""Prompt Sanitizer & Anti-Injection Guardrail Service.
Protects AI agents and financial checkout flows against adversarial jailbreaks,
system prompt overrides, and unauthorized discount manipulation.
"""

import re
import logging
from typing import Any

logger = logging.getLogger(__name__)

# Known prompt-injection and jailbreak vectors
_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(?:all\s+)?(?:previous|prior|above|system\s+)?(?:instructions|prompts|rules)", re.IGNORECASE),
    re.compile(r"disregard\s+(?:all\s+)?(?:previous|prior|system\s+)?(?:instructions|rules|constraints)", re.IGNORECASE),
    re.compile(r"(?:system\s*override|you\s+are\s+now\s+(?:in\s+)?(?:god|admin|developer|jailbreak)\s+mode)", re.IGNORECASE),
    re.compile(r"(?:bypass\s+(?:budget|guardrail|payment|checkout|security)|disable\s+guardrails?)", re.IGNORECASE),
    re.compile(r"(?:apply|give|generate|create)\s+(?:a\s+)?(?:100%|99%|90%|80%|free)\s+(?:[a-zA-Z0-9_\-]+\s+)?(?:discount|coupon|promo)", re.IGNORECASE),
    re.compile(r"(?:set\s+price\s+to\s+0|make\s+(?:it|item|total)\s+free|price\s+(?:is\s+now|set\s+to)\s+₹?[01])", re.IGNORECASE),
    re.compile(r"(?:<\|im_start\|>|<\|im_end\|>|\[INST\]|\[/INST\]|<<SYS>>|<</SYS>>|system:)", re.IGNORECASE),
    re.compile(r"(?:i\s+am\s+(?:the\s+)?(?:store\s+owner|admin|developer|tester)|developer\s+testing)", re.IGNORECASE),
    re.compile(r"(?:base64\s*:|execute\s+base64)", re.IGNORECASE),
    re.compile(r"(?:admin_token|root_authorized|force\s+order\s+total)", re.IGNORECASE),
    re.compile(r"(?:!\[.*?\]\(https?://|javascript:)", re.IGNORECASE),
    re.compile(r"(?:hypothetically.*?(?:price\s+set\s+to\s+0|free|coupon))", re.IGNORECASE),
]


class PromptSanitizer:
    """Detects and neutralizes prompt-injection attacks on conversational shopping agents."""

    @staticmethod
    def sanitize_customer_input(raw_text: str) -> dict[str, Any]:
        """Analyze and sanitize raw user input before sending to LLM.
        
        Returns:
            {
                "is_safe": bool,
                "sanitized_text": str,
                "flags": list[str],
                "was_modified": bool,
            }
        """
        if not raw_text or not isinstance(raw_text, str):
            return {"is_safe": True, "sanitized_text": "", "flags": [], "was_modified": False}

        flags = []
        sanitized = raw_text

        # 1. Check against injection patterns
        for pattern in _INJECTION_PATTERNS:
            match = pattern.search(sanitized)
            if match:
                matched_phrase = match.group(0)
                flags.append(f"Adversarial prompt injection attempt: '{matched_phrase}'")
                # Strip or neutralize the matched injection phrase
                sanitized = pattern.sub("[filtered_instruction]", sanitized)

        # 2. Strip dangerous control delimiters
        control_delimiters = ["<|im_start|>", "<|im_end|>", "[INST]", "[/INST]", "<<SYS>>", "<</SYS>>"]
        for delim in control_delimiters:
            if delim in sanitized:
                sanitized = sanitized.replace(delim, "")
                flags.append(f"Stripped control token '{delim}'")

        is_safe = len(flags) == 0
        if not is_safe:
            logger.warning(
                "Security Alert: Blocked prompt injection in message: '%s'. Flags: %s",
                raw_text[:80],
                flags,
            )

        return {
            "is_safe": is_safe,
            "sanitized_text": sanitized.strip(),
            "flags": flags,
            "was_modified": sanitized != raw_text,
        }


prompt_sanitizer = PromptSanitizer()
