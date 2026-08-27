# 🎬 MerchantMind — 5-Minute Pitch & Demo Script

> **Track 01**: AI Growth & Agentic Commerce | Razorpay AI Buildathon 2026  
> **Total Target Duration**: ≤ 4 minutes 45 seconds (5 min max limit)

---

## ⏱️ Timeline & Scene Breakdown

```
[0:00 - 0:35] Scene 1: The Problem & The Solution
[0:35 - 1:10] Scene 2: High-Level Architecture
[1:10 - 2:40] Scene 3: Live Demo — Conversational Checkout & Smart Upsell
[2:40 - 3:30] Scene 4: Live Demo — Razorpay Payment & Webhook Capture
[3:30 - 4:10] Scene 5: Guardrails (Budget Enforcement & Full Audit Trail)
[4:10 - 4:45] Scene 6: WhatsApp Commerce & Multi-Tenant Closing
```

---

## 🎙️ Detailed Cue-by-Cue Walkthrough

### 🎬 Scene 1: Problem & Solution (0:00 - 0:35)
- **Visual**: Show Landing Page ([http://localhost:3000](http://localhost:3000)) with glowing glassmorphism hero section.
- **Narration**:
  > *"E-commerce storefronts today are static. When a customer searches for a birthday cake, they scroll through endless filters, guess portions, miss complementary add-ons, and abandon their carts.*  
  > *Meet **MerchantMind** — an autonomous AI shopping and growth agent built on Razorpay and Groq. It turns any merchant's catalog into a conversational shopping experience that understands natural language, recommends items with clear reasoning, suggests smart upsells, and completes payments instantly with Razorpay."*

---

### 🎬 Scene 2: System Architecture (0:35 - 1:10)
- **Visual**: Show architecture diagram from `docs/architecture.md` or README.
- **Narration**:
  > *"Under the hood, MerchantMind is built with a production-grade containerized stack:*
  > 1. *Next.js 16 frontend with real-time payment status polling.*
  > 2. *FastAPI backend orchestrating multi-turn Groq tool calls with model fallback.*
  > 3. *Meta WhatsApp Cloud API v21.0 for conversational messaging.*
  > 4. *Razorpay Order APIs and cryptographic HMAC webhook verification.*
  > 5. *PostgreSQL capturing an immutable audit trail of every agent decision and transaction."*

---

### 🎬 Scene 3: Live Conversational Checkout & Smart Upsell (1:10 - 2:40)
- **Visual**: Click "Launch Live Store" ➔ Enter Chat Store ([http://localhost:3000/chat](http://localhost:3000/chat)).
- **Action 1**: Type in chat:
  ```text
  "I want a chocolate cake for my friend's birthday party, my budget is under ₹800"
  ```
- **Narration**:
  > *"Notice how the agent instantly parses the user's intent: category is Cake, flavor is Chocolate, occasion is Birthday, and budget is capped at ₹800.*  
  > *It recommends the Belgian Truffle Cake and explicitly explains WHY — detailing portion size, rich ganache layers, and that it costs ₹650, safely under the ₹800 budget."*
- **Action 2**: Click **"Add to Cart"** on the cake card.
- **Action 3**: Type:
  ```text
  "What else should I get to complete the birthday party?"
  ```
- **Narration**:
  > *"Look at the smart upsell engine at work! Because we have a birthday cake in our cart and ₹150 remaining in our ₹800 budget, the agent proactively recommends the Birthday Candles Set (₹50) and Party Balloons (₹100) — pairing the occasion while strictly respecting our budget."*
- **Action 4**: Click **"Add to Cart"** on the candles.

---

### 🎬 Scene 4: Razorpay Payment & Webhook Confirmation (2:40 - 3:30)
- **Visual**: Show cart total at ₹700 (Cake ₹650 + Candles ₹50).
- **Action 1**: Click the glowing button **"Pay ₹700 with Razorpay"** (or type *"I want to checkout now"*).
- **Narration**:
  > *"When the customer is ready, MerchantMind creates a Razorpay Order and generates an instant, secure Payment Link."*
- **Action 2**: Click **"Pay Now with Razorpay"** in the chat bubble or cart sidebar ➔ Razorpay Test Checkout opens.
- **Action 3**: Complete test payment using Razorpay card `4111 1111 1111 1111`, any future expiry, and OTP `123456`.
- **Narration**:
  > *"As soon as the payment is processed, Razorpay dispatches a signed webhook. Our backend verifies the cryptographic HMAC-SHA256 signature, marks the order as PAID, and our frontend live-updates with payment confirmation and confetti!"*

---

### 🎬 Scene 5: Guardrails & Full Audit Trail (3:30 - 4:10)
- **Visual 1**: Show Budget Guardrail.
  - In chat, type: *"Add a ₹500 champagne box to my cart and checkout"* (exceeds stated budget).
  - Show the guardrail alert: *"Budget Guardrail: Cart total exceeds your stated budget limit of ₹800."*
- **Visual 2**: Switch tab to API Docs ([http://localhost:8000/docs#/Orders/get_order_audit_trail_endpoint_api_orders__order_id__audit_get](http://localhost:8000/docs)) or curl `GET /api/orders/{id}/audit`.
- **Narration**:
  > *"Enterprise trust requires strict guardrails. If an agent tries to push an order over the customer's stated budget, our hard validation blocks checkout and records a `budget_violation` event.*  
  > *Every agent decision, catalog query, Razorpay API payload, and webhook receipt is logged with reasoning in our immutable audit trail API."*

---

### 🎬 Scene 6: WhatsApp Commerce & Closing (4:10 - 4:45)
- **Visual**: Show WhatsApp webhook logs or ngrok terminal logs with incoming `GET /api/webhooks/whatsapp` and `POST /api/campaigns/dispatch`.
- **Visual**: Switch merchant in header dropdown to show multi-tenant store isolation ("Sweet Bakes" vs "Fashion Hub").
- **Narration**:
  > *"Finally, MerchantMind extends beyond the web — customers can complete the exact same conversational checkout directly on WhatsApp via Meta Cloud API, and merchants can re-engage dormant customers with automated personalized discount campaigns.*  
  > *MerchantMind turns every Razorpay merchant into an autonomous growth powerhouse. Thank you!"*

---

## 💡 Pro Tips for Video Recording
1. **Screen Resolution**: Set display to 1080p (1920x1080) for sharp readability.
2. **Audio**: Use a quiet room and headphones/mic for crisp voiceover.
3. **Cursor**: Move the mouse smoothly to draw the viewer's eye to key buttons (e.g. Add to Cart, Pay Now).
4. **Duration Check**: Keep it right around 4:30 to 4:45 so you are comfortably under the 5:00 maximum limit.
