# 🎬 MerchantMind — Demo Script

> 5-minute demo video. Updated after each phase.

---

## Video Specs
- **Max Duration**: 5:00
- **Format**: Screen recording + voice narration
- **Show**: Working product, architecture, one failure handled

---

## Script v1 (Draft — will evolve)

| Time | Visual | Narration |
|------|--------|-----------|
| 0:00–0:30 | Stats on screen: 85% cart abandonment, ₹2.5L Cr WhatsApp commerce, rising CAC | *"Small Razorpay merchants face 3 problems: customers abandon checkout, AI buyers can't find them, and reacquiring lost customers costs 5x more. MerchantMind solves all three."* |
| 0:30–1:00 | Architecture diagram | *"MerchantMind has 4 modules: AI-readable Catalog, Conversational Checkout, Upsell Agent, and Campaign Orchestrator. Powered by Groq's llama-3.3-70b, payments via Razorpay, messages via WhatsApp."* |
| 1:00–1:45 | Upload bakery menu → Schema.org JSON-LD generated | *"This bakery had a PDF menu. MerchantMind converts it to an agent-readable catalog. Now any AI can discover and transact with this merchant."* |
| 1:45–3:00 | Chat: "I want a chocolate birthday cake under ₹800" → Options → Upsell candles → Razorpay payment → Confirmed | *"Customer says what they want. Agent finds matching products, suggests a birthday combo, creates a Razorpay order. From intent to payment in 90 seconds. Order value: ₹650 → ₹999."* |
| 3:00–3:45 | WhatsApp demo: receive message → agent responds → payment link → paid | *"Same flow works on WhatsApp — 550M Indian users. The agent handles natural language, even Hinglish."* |
| 3:45–4:15 | Audit trail + intentional payment failure → graceful handling | *"Every decision is audited. If payment fails, the agent retries. Budget guardrails prevent overspending."* |
| 4:15–5:00 | System design diagram + Docker + CI/CD + big picture | *"Dockerized, CI/CD on GitHub Actions, multi-tenant architecture. This makes Razorpay merchants AI-ready for the agentic commerce future."* |

---

## Key Demo Moments to Nail

1. **The "wow"**: Natural language → instant product recommendations
2. **The money moment**: Razorpay payment completing in test mode
3. **The depth**: Upsell increasing order value by 54%
4. **The reliability**: Failure handled gracefully
5. **The architecture**: Docker + CI/CD + multi-tenant

---

## Notes
- Practice at least 2x before recording
- Keep energy HIGH in narration
- Show REAL transactions (test mode), not slides
- End with the Razorpay connection: "Razorpay becomes the commerce layer for the AI economy"
