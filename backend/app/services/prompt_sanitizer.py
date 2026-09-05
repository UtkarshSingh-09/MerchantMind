"""Prompt Sanitizer & Anti-Injection Guardrail Service.
Protects AI agents and financial checkout flows against adversarial jailbreaks,
system prompt overrides, unauthorized discount manipulation, and secret data exfiltration.
"""

import re
import unicodedata
import logging
from typing import Any

logger = logging.getLogger(__name__)

# Known prompt-injection and jailbreak vectors
_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(?:all\s+)?(?:previous\s+|prior\s+|above\s+|system\s+)*(?:instructions|prompts|rules)", re.IGNORECASE),
    re.compile(r"disregard\s+(?:all\s+)?(?:previous\s+|prior\s+|above\s+|system\s+)*(?:instructions|rules|constraints)", re.IGNORECASE),
    re.compile(r"(?:system\s*override|you\s+are\s+now\s+(?:in\s+)?(?:god|admin|developer|jailbreak)\s+mode)", re.IGNORECASE),
    re.compile(r"(?:bypass\s+(?:budget|guardrail|payment|checkout|security)|disable\s+guardrails?)", re.IGNORECASE),
    re.compile(r"(?:apply|give|generate|create)\s+(?:a\s+)?(?:100%|99%|90%|80%|free)\s+(?:[a-zA-Z0-9_\-]+\s+)?(?:discount|coupon|promo)", re.IGNORECASE),
    re.compile(r"(?:set\s+price\s+to\s+0|make\s+(?:it|item|total)\s+free|price\s+(?:is\s+now|set\s+to)\s+₹?[01])", re.IGNORECASE),
    re.compile(r"(?:<\|im_start\|>|<\|im_end\|>|\[INST\]|\[/INST\]|<<SYS>>|<</SYS>>|system:)", re.IGNORECASE),
    re.compile(r"(?:i\s+am\s+(?:the\s+)?(?:store\s+owner|admin|developer|tester)|developer\s+testing)", re.IGNORECASE),
    re.compile(r"(?:base64\s*:|execute\s+base64)", re.IGNORECASE),
    re.compile(r"(?:admin_token|root_authorized|force\s+order\s+total)", re.IGNORECASE),
    re.compile(r"(?:reveal|print|show|output)\s+(?:system\s+prompt|secret|instructions|developer\s+mode)", re.IGNORECASE),
    re.compile(r"(?:dan\s+mode|jailbreak\s+prompt|jailbreak\s*:)", re.IGNORECASE),
    re.compile(r"(?:act\s+as\s+(?:root|admin|system|developer))", re.IGNORECASE),
    re.compile(r"(?:forget\s+(?:everything|previous|all|prior))", re.IGNORECASE),
    re.compile(r"(?:!\[.*?\]\(https?://|javascript:)", re.IGNORECASE),
    re.compile(r"(?:hypothetically.*?(?:price\s+set\s+to\s+0|free|coupon))", re.IGNORECASE),
]

# Patterns for redacting sensitive secrets and data exfiltration in agent responses
_LEAK_PATTERNS = [
    (re.compile(r"rzp_(?:test|live)_[a-zA-Z0-9]{14,24}"), "[REDACTED_RAZORPAY_KEY]"),
    (re.compile(r"mm_live_[a-zA-Z0-9]{24,64}"), "[REDACTED_MERCHANT_KEY]"),
    (re.compile(r"(?:postgresql|postgres|redis|rediss)://[^\s\"']+"), "[REDACTED_CONNECTION_URI]"),
    (re.compile(r"!\[(?:[^\]]*)\]\((https?://[^\)]+)\)"), "[filtered_image_exfiltration]"),
    (re.compile(r"(?:SYSTEM\s+PROMPT|System\s+Instructions|Secret\s+Key)\s*:\s*[^\n]+", re.IGNORECASE), "[filtered_system_instruction]"),
]

# Invisible zero-width and control characters used for obfuscation bypasses
_ZERO_WIDTH_CHARS = re.compile(r"[\u200B-\u200D\uFEFF\u00AD\u2060]")


class PromptSanitizer:
    """Detects and neutralizes prompt-injection attacks and prevents secret exfiltration in AI agents."""

    @staticmethod
    def deobfuscate_text(text: str) -> str:
        """Strip zero-width characters and normalize unicode homoglyphs via NFKC."""
        if not text:
            return ""
        # 1. Normalize unicode (e.g. Cyrillic lookalikes to Latin standard)
        normalized = unicodedata.normalize("NFKC", text)
        # 2. Strip invisible zero-width spaces/joiners
        deobfuscated = _ZERO_WIDTH_CHARS.sub("", normalized)
        return deobfuscated

    @classmethod
    def sanitize_customer_input(cls, raw_text: str) -> dict[str, Any]:
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
        # Pre-normalize for pattern checking to stop obfuscated bypasses
        deobfuscated = cls.deobfuscate_text(raw_text)
        sanitized = deobfuscated

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

    @staticmethod
    def sanitize_agent_output(raw_text: str) -> dict[str, Any]:
        """Examine LLM output before delivery to client to prevent secret leakage or markdown image exfiltration.
        
        Returns:
            {
                "is_safe": bool,
                "sanitized_text": str,
                "redactions": list[str],
                "was_modified": bool,
            }
        """
        if not raw_text or not isinstance(raw_text, str):
            return {"is_safe": True, "sanitized_text": "", "redactions": [], "was_modified": False}

        sanitized = raw_text
        redactions = []

        for pattern, replacement in _LEAK_PATTERNS:
            matches = pattern.findall(sanitized)
            if matches:
                redactions.append(f"Redacted sensitive pattern: {pattern.pattern}")
                sanitized = pattern.sub(replacement, sanitized)

        is_safe = len(redactions) == 0
        if not is_safe:
            logger.warning("Security Alert: Redacted sensitive leaks in agent response: %s", redactions)

        return {
            "is_safe": is_safe,
            "sanitized_text": sanitized,
            "redactions": redactions,
            "was_modified": sanitized != raw_text,
        }


prompt_sanitizer = PromptSanitizer()
