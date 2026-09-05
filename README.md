<div align="center">

<img width="100%" src="assets/hero.svg" alt="MerchantMind Hero" />

<br/>

`Autonomous AI Shopping & Growth Agent`<br/>
`Multi-Agent AI · Razorpay Native · Groq LLM · Conversational Commerce`

<br/>

[![Python](https://img.shields.io/badge/Python-3.12-D97706?style=for-the-badge&logo=python&logoColor=white&labelColor=151515)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-991B1B?style=for-the-badge&logo=fastapi&logoColor=white&labelColor=151515)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-16-FBBF24?style=for-the-badge&logo=next.js&logoColor=white&labelColor=151515)](https://nextjs.org)
[![Groq](https://img.shields.io/badge/Groq-Llama_3.3_70B-D97706?style=for-the-badge&labelColor=151515)](https://groq.com)
[![Razorpay](https://img.shields.io/badge/Razorpay-Payment_Links-2962FF?style=for-the-badge&logo=razorpay&logoColor=white&labelColor=151515)](https://razorpay.com)
[![Deepgram](https://img.shields.io/badge/Deepgram-Aura_TTS-13EF93?style=for-the-badge&logo=deepgram&logoColor=black&labelColor=151515)](https://deepgram.com)
[![License](https://img.shields.io/badge/License-MIT-FBBF24?style=for-the-badge&labelColor=151515)](LICENSE)

<br/>

**Track 01 · AI Growth & Agentic Commerce · Razorpay AI Buildathon 2026**

[![Live Demo](https://img.shields.io/badge/Live_Demo-Explore_Platform-00C7B7?style=for-the-badge&logo=netlify&logoColor=white&labelColor=18181b)](https://merchantmind-ai.netlify.app)
&nbsp;
[![Architecture](https://img.shields.io/badge/Architecture-System_Design-F59E0B?style=for-the-badge&logo=gitbook&logoColor=white&labelColor=18181b)](ARCHITECTURE.md)
&nbsp;
[![Problems Log](https://img.shields.io/badge/Problems_Log-16_Solved-EF4444?style=for-the-badge&logo=target&logoColor=white&labelColor=18181b)](docs/problems.md)
&nbsp;
[![Report Bug](https://img.shields.io/badge/Report_Bug-New_Issue-10B981?style=for-the-badge&logo=github&logoColor=white&labelColor=18181b)](https://github.com/UtkarshSingh-09/MerchentMind-/issues/new?template=bug_report.md)
&nbsp;
[![Request Feature](https://img.shields.io/badge/Request_Feature-Submit_Idea-8B5CF6?style=for-the-badge&logo=github&logoColor=white&labelColor=18181b)](https://github.com/UtkarshSingh-09/MerchentMind-/issues/new?template=feature_request.md)

---

</div>

<img width="100%" src="assets/system_overview.svg" alt="System Overview" />

---

## 🔴 The Problem

Traditional e-commerce storefronts are **static, menu-driven, and passive**. Customers browse, scroll, get overwhelmed, and abandon carts.

| Pain Point | Real-World Impact | Merchant Loss |
|---|---|---|
| **Choice Overload** | 200+ local stores × 5,000+ items = decision paralysis. Users drop off within 45 seconds. | High customer acquisition cost wasted with zero conversion. |
| **Zero Upselling Intelligence** | Static checkout forms cannot infer that a birthday cake needs candles and balloons. | Merchants surrender 15%–30% in high-margin average order value (AOV). |
| **Fragmented Payment UX** | Copy-pasting UPI handles or dealing with broken redirection gateways causes cart drop-offs. | Up to 40% checkout abandonment at the final payment step. |
| **Monolithic Single-Channel Silos** | Shoppers spend hours on WhatsApp, Telegram, and voice; merchants are locked to a static web form. | Inability to engage customers in their native conversational channel. |
| **Passive Retention** | Lapsed customers receive generic, unsegmented discount blasts that get flagged as spam. | Zero automated reactivation for high-LTV dormant shoppers. |

> **The bottom line:** Independent merchants lose sales not from lack of product quality, but because they lack an *autonomous sales agent* that understands customer intent, curates options, upsells intelligently, and closes payments instantly.

---

## 🟢 The Solution

**MerchantMind** transforms passive product catalogs into **autonomous, conversational commerce engines**. It acts as an elite digital sales concierge that *reasons, recommends, cross-sells within strict budgets, orchestrates atomic checkouts, and tracks deliveries*.

```
   "I need an eggless birthday cake     ┌────────────────────────────────────────────────┐
    under ₹700 in Indiranagar"    ──▶   │           🧠 MerchantMind Autonomous Agent      │
                                        │                                                │
                                        │  1. Parse intent & geographic proximity        │
                                        │  2. Apply 0ms regex & NLP budget cap (₹700)    │
                                        │  3. Query 200+ Bangalore stores in <650ms      │
                                        │  4. Pair occasion upsells (Candles ₹60)        │
                                        │  5. Reserve stock via PostgreSQL row-lock      │
                                        │  6. Generate Razorpay Payment Link (atomic)    │
                                        │  7. Verify HMAC webhook & initiate tracking    │
                                        └────────────────────────────────────────────────┘
```

**One natural language prompt or voice command. Full checkout. Zero friction.**

---

## ⚔️ Architectural Comparison

How MerchantMind compares against traditional e-commerce platforms and basic conversational wrappers:

| Capability | Traditional E-Commerce (Shopify / WooCommerce) | Generic RAG Chatbot (LangChain / GPT Wrapper) | MerchantMind Autonomous Agent |
|---|---|---|---|
| **Interaction Paradigm** | Static menus, manual faceted filters, click-and-scroll | Chat interface with text-only product links | Natural language voice & multi-turn dialog with rich visual cards |
| **Discovery Latency** | High cognitive overhead (minutes of searching) | Slow (3s–8s prompt lookups, prone to hallucinations) | Sub-second (<650ms) ReAct loop with cached catalog aggregations |
| **Budget Enforcement** | Client-side visual price sliders only | Advisory only; frequently suggests items exceeding budget | **Hard Deterministic Guardrail**: mathematically blocks overbudget checkouts |
| **Cross-Selling / Upsell** | Hardcoded rule tables ("Customers also bought...") | Unconstrained suggestions ignoring remaining user budget | **Context-Aware Occasion Engine** bounded by remaining customer budget |
| **Payment Integration** | Standard multi-page checkout redirection | External markdown links to generic store homepages | **Native Razorpay 2PC Saga**: Server-side orders + short links + HMAC verification |
| **Inventory Concurrency** | Prone to overselling under flash sales without strict locks | No inventory awareness or direct transactional coupling | **Pessimistic Row-Level Locks** (`SELECT ... FOR UPDATE`) with auto-rollback |
| **Voice Experience** | None | Generic browser speech-to-text without pronunciation tuning | **Deepgram Flux Meena** + Indian English phonetic normalizer + barge-in |
| **Safety & Redaction** | Standard form validation | Vulnerable to system prompt leaks and jailbreak manipulation | **NFKC Unicode Normalizer**, regex injection sanitizer & key-redaction filters |

---

## 🏗️ Architecture

### High-Level System Topology

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                     CLIENT LAYER                                       │
│   ┌────────────────────────┐  ┌─────────────────────────┐  ┌───────────────────────┐   │
│   │   Next.js 16 Web UI    │  │    Telegram Bot API     │  │  Ambient Voice Engine │   │
│   │ (App Router + Three.js)│  │ (Inline Webhook Handler)│  │  (Web Speech + Aura)   │   │
│   └───────────┬────────────┘  └────────────┬────────────┘  └───────────┬───────────┘   │
└───────────────┼────────────────────────────┼───────────────────────────┼───────────────┘
                │                            │                           │
                ▼                            ▼                           ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              REVERSE PROXY & API GATEWAY                               │
│                         Nginx (SSL Termination + Rate Limiting)                        │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                         APPLICATION LAYER (FastAPI + Uvicorn)                          │
│                                                                                        │
│   ┌────────────────────────────────────────────────────────────────────────────────┐   │
│   │                           MULTI-AGENT ORCHESTRATOR                             │   │
│   │   ┌───────────────┐     ┌────────────────┐     ┌───────────────────────────┐   │   │
│   │   │  AgentRouter  │ ──▶ │ DiscoveryAgent │ ──▶ │ ShoppingAgent             │   │   │
│   │   │ (Intent Clf)  │     │ (Cross-Store)  │     │ (In-Store Cart + Upsell)  │   │   │
│   │   └───────┬───────┘     └────────────────┘     └─────────────┬─────────────┘   │   │
│   │           │                                                  │                 │   │
│   │           ▼                                                  ▼                 │   │
│   │   ┌───────────────┐                             ┌──────────────────────────┐   │   │
│   │   │ MerchantAgent │                             │ 3-Phase Checkout Saga    │   │   │
│   │   │ (Analytics)   │                             │ (2PC Razorpay Engine)    │   │   │
│   │   └───────────────┘                             └──────────────────────────┘   │   │
│   └────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                        │
│   ┌─────────────────────┐  ┌──────────────────────┐  ┌─────────────────────────────┐   │
│   │  Budget Guardrail   │  │ Prompt Sanitizer     │  │ Resilience Circuit Breaker  │   │
│   │ (Deterministic Cap) │  │ (Adversarial Defense)│  │ (Groq Llama 70B ➔ 8B Failover)│   │
│   └─────────────────────┘  └──────────────────────┘  └─────────────────────────────┘   │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
                ┌───────────────────────────┼───────────────────────────┐
                ▼                           ▼                           ▼
┌───────────────────────────────┐ ┌───────────────────┐ ┌───────────────────────────────┐
│        AI INFERENCE           │ │   PAYMENT CLOUD   │ │          DATA LAYER           │
│  Groq Cloud Llama 3.3 70B     │ │  Razorpay API     │ │  PostgreSQL 16 (Row-Locked)   │
│  Deepgram Voice API (Flux)    │ │  Orders + Links   │ │  Redis 7 (Sliding Window &    │
│  Llama 3.1 8B (Fallback)      │ │  HMAC Webhooks    │ │           Session Caches)     │
└───────────────────────────────┘ └───────────────────┘ └───────────────────────────────┘
```

### End-to-End Request Lifecycle

```
Customer Message / Voice ──▶ Audio Transcribe / Text Ingestion
                                         │
                                         ▼
                             PromptSanitizer.sanitize()
                             (Deobfuscates NFKC, strips zero-width chars, blocks jailbreaks)
                                         │
                                         ▼
                             BudgetExtractor.extract()
                             (0ms Regex fast-path: "under 700" ➔ ₹700.00 hard limit)
                                         │
                                         ▼
                                    AgentRouter
                                         │
                     ┌───────────────────┴───────────────────┐
                     ▼                                       ▼
              DiscoveryAgent                           ShoppingAgent
        (No store locked; compares               (Store locked; manages cart,
         200+ Bangalore merchants)                computes remaining budget)
                     │                                       │
                     ▼                                       ▼
        Semantic Catalog Match                     Contextual Upsell Engine
        (Tokenizes queries, handles               (Cake detected ➔ pairs candles
         food & regional synonyms)                 only if cart + upsell ≤ budget)
                     │                                       │
                     └───────────────────┬───────────────────┘
                                         ▼
                            User Confirms Checkout Intent
                                         │
                                         ▼
                            CheckoutSaga.execute_checkout()
                            ├─ Step 1: Check Idempotency Key (Redis)
                            ├─ Step 2: Phase 1 — SELECT ... FOR UPDATE (Row-Lock)
                            ├─ Step 3: Phase 2 — Razorpay Order & Payment Link
                            └─ Step 4: Phase 3 — Commit Order & Log Audit Trail
                                         │
                                         ▼
                            Razorpay Payment Completed
                                         │
                                         ▼
                            POST /api/webhooks/razorpay
                            (Raw-byte HMAC-SHA256 signature verification)
                                         │
                                         ▼
                        Order State: PAID ➔ Live Tracking Initiated
```

---

## 🤖 Multi-Agent Intelligence

MerchantMind decomposes complex commerce operations across specialized agents rather than relying on a brittle single prompt:

| Agent | Core Model | Primary Role | Executable Tools |
|---|---|---|---|
| **AgentRouter** | Llama 3.1 8B | Lightweight, low-latency intent classification | `classify_routing_intent()` |
| **DiscoveryAgent** | Llama 3.3 70B | Cross-catalog exploration across 200+ stores | `search_all_merchants()`, `get_merchant_info()`, `search_merchant_products()` |
| **ShoppingAgent** | Llama 3.3 70B | In-store cart management, upselling, and checkout | `add_to_cart()`, `remove_from_cart()`, `get_cart()`, `clear_cart()`, `execute_checkout()` |
| **MerchantAgent** | Llama 3.3 70B | Business intelligence, stock auditing & campaigns | `get_store_analytics()`, `dispatch_campaign()` |
| **CheckoutSaga** | Deterministic Engine | Atomic two-phase commit payment orchestrator | Razorpay SDK Orders & Payment Links APIs |

---

## 🎙️ Autonomous Voice Engine & Indian English NLP

MerchantMind features an **ambient, hands-free voice engine** specifically tuned for Indian conversational commerce:

```
 User Voice Input ──▶ Web Speech STT / Whisper ──▶ Phonetic Normalizer ──▶ ReAct Agent
                                                                               │
 Audio Output ◀── Deepgram Flux Meena (flux-meena-en) ◀── Concise TTS Formatter ┘
```

1. **Indian Retail & Geographical Phonetic Normalizer**:
   A built-in dictionary in [`voice-manager.ts`](file:///Users/utkarshsingh/Desktop/Razorpay_hackathon/frontend/src/lib/voice-manager.ts) converts Indian food terms, Bangalore localities, and currency symbols into natural phonetic representations for seamless speech synthesis:
   - Bangalore Localities: `Indiranagar` ➔ *"Indira Nagar"*, `Koramangala` ➔ *"Kora-mangala"*, `HSR` ➔ *"H S R"*, `Whitefield` ➔ *"White-field"*.
   - Food & Dishes: `Biryani` ➔ *"Beer-yaani"*, `Paneer` ➔ *"Puh-neer"*, `Gulab Jamun` ➔ *"Goo-laab Jaa-moon"*, `Dosa` ➔ *"Dho-saa"*.
   - Currency: `₹500` / `Rs. 500` ➔ *"500 rupees"*.
2. **Adaptive Silence Auto-Dispatch (2.2s–3.0s Buffer)**:
   Standard voice agents cut off speech after 800ms of hesitation. MerchantMind dynamically adjusts silence thresholds based on sentence completeness, allowing natural pauses while customers contemplate flavors or quantities.
3. **Web Audio Autoplay Unlocker**:
   Bypasses browser autoplay blocks via an invisible user-gesture audio context primer primed on the first tap.
4. **Instant Voice Barge-In**:
   Allows the user to speak at any moment; active Deepgram TTS audio streams abort instantly when new user speech is detected.

---

## ⚡ 3-Phase Distributed Checkout Saga (2PC)

To prevent financial discrepancies, phantom orders, and overselling, checkout is executed as an **atomic 3-phase saga** with automated compensation in [`checkout_saga.py`](file:///Users/utkarshsingh/Desktop/Razorpay_hackathon/backend/app/services/checkout_saga.py):

```
       Phase 1                     Phase 2                     Phase 3
  [ Inventory Lock ]         [ Razorpay Gateway ]         [ Commit & Audit ]
 ┌──────────────────┐       ┌────────────────────┐       ┌──────────────────┐
 │ SELECT ...       │       │ POST /v1/orders    │       │ Commit DB Order  │
 │ FOR UPDATE       │ ────▶ │ POST /payment_links│ ────▶ │ Log Audit Event  │
 │ (Deduct Stock)   │       │ (Atomic Integer ₹) │       │ Status: PENDING  │
 └──────────────────┘       └────────────────────┘       └──────────────────┘
          │                           │
          ▼ (On Failure)              ▼ (On Failure)
 ┌──────────────────┐       ┌────────────────────┐
 │  ROLLBACK DB     │ ◀──── │ Execute Saga       │
 │  Restore Stock   │       │ Compensation       │
 └──────────────────┘       └────────────────────┘
```

- **Phase 1 (Stock Reservation)**: Acquires pessimistic row-level database locks on product rows (`SELECT ... FOR UPDATE`). If any line item has insufficient stock, the transaction is rejected immediately.
- **Phase 2 (Razorpay Order & Payment Link Creation)**: Communicates with the Razorpay API to generate an authoritative order ID and short payment URL. Amounts are strictly computed in integer paise (`int(round(amount * 100))`).
- **Phase 3 (Commit & Audit)**: Commits the order record with status `pending_payment` and persists an immutable audit entry (`ORDER_CREATED`).
- **Automated Compensation**: If Razorpay API times out or payment link creation fails, the saga catches the exception, automatically increments back the reserved stock count, marks the order as `failed`, and logs a `STOCK_COMPENSATED` audit event.

---

## 🛡️ Deterministic Guardrails & Security Matrix

MerchantMind layers deterministic software constraints around probabilistic LLM inference:

| Security Layer | Threat Model | Enforcement Mechanism | Codebase Reference |
|---|---|---|---|
| **Hard Budget Validator** | LLM hallucinating items beyond customer limit | Dual-stage: 0ms regex parser + arithmetic check (`cart + upsell <= budget`) | [`budget_extractor.py`](file:///Users/utkarshsingh/Desktop/Razorpay_hackathon/backend/app/services/budget_extractor.py) |
| **Single-Store Multi-Tenant Guardrail** | Accidental multi-store cart mixing | Enforces strict single-merchant lock per order; blocks mixing across stores | [`shopping_agent.py`](file:///Users/utkarshsingh/Desktop/Razorpay_hackathon/backend/app/agents/shopping_agent.py) |
| **Adversarial Prompt Defense** | Jailbreaks, "DAN mode", roleplay, "set price to 0" | Regex pattern scanner + NFKC unicode normalization + zero-width char stripper | [`prompt_sanitizer.py`](file:///Users/utkarshsingh/Desktop/Razorpay_hackathon/backend/app/services/prompt_sanitizer.py) |
| **Secret Redaction Filter** | Leaking Razorpay keys or DB connection URIs | Post-processing regex filter redacting `rzp_test_*`, `mm_live_*`, and DB strings | [`prompt_sanitizer.py`](file:///Users/utkarshsingh/Desktop/Razorpay_hackathon/backend/app/services/prompt_sanitizer.py) |
| **Webhook Signature Verification** | Forged payment confirmation callbacks | HMAC-SHA256 verification against raw request binary bytes | [`webhooks.py`](file:///Users/utkarshsingh/Desktop/Razorpay_hackathon/backend/app/routes/webhooks.py) |
| **Sliding Window Rate Limiter** | DoS / API key exhaustion attacks | Redis sliding-window counter tracking client IP and forwarded proxy headers | [`rate_limiter.py`](file:///Users/utkarshsingh/Desktop/Razorpay_hackathon/backend/app/services/rate_limiter.py) |
| **Idempotency Engine** | Duplicate checkout submission or webhook replay | Deterministic hashing of `(conversation_id, merchant_id, items, total)` | [`idempotency_service.py`](file:///Users/utkarshsingh/Desktop/Razorpay_hackathon/backend/app/services/idempotency_service.py) |

---

## 💳 Razorpay Integration Deep Dive

MerchantMind is built natively upon the full Razorpay payment stack:

### Payment Flow

```
┌────────────┐            ┌──────────────┐            ┌──────────────────────┐
│  Customer  │            │ MerchantMind │            │     Razorpay API     │
│  (Browser) │            │   Backend    │            │                      │
└─────┬──────┘            └──────┬───────┘            └──────────┬───────────┘
      │                          │                               │
      │  "Checkout"              │                               │
      │─────────────────────────▶│                               │
      │                          │  POST /v1/orders              │
      │                          │  amount: 65000 (paise)        │
      │                          │──────────────────────────────▶│
      │                          │                               │
      │                          │  order_id: order_Q123...      │
      │                          │◀──────────────────────────────│
      │                          │                               │
      │                          │  POST /v1/payment_links       │
      │                          │──────────────────────────────▶│
      │                          │                               │
      │                          │  short_url: https://rzp.io/...│
      │                          │◀──────────────────────────────│
      │                          │                               │
      │  Razorpay Payment Link   │                               │
      │◀─────────────────────────│                               │
      │                                                          │
      │  Opens Razorpay Standard Checkout                        │
      │─────────────────────────────────────────────────────────▶│
      │                                                          │
      │  UPI / Card / Netbanking Captured                        │
      │─────────────────────────────────────────────────────────▶│
      │                          │                               │
      │                          │  POST /api/webhooks/razorpay  │
      │                          │  (X-Razorpay-Signature)       │
      │                          │◀──────────────────────────────│
      │                          │                               │
      │                          │  1. Verify HMAC (Raw Bytes)   │
      │                          │  2. Order Status ➔ PAID       │
      │                          │  3. Calculate Delivery ETA    │
      │                          │                               │
      │  Poll: /api/orders/{id}  │                               │
      │─────────────────────────▶│                               │
      │  status: "paid"          │                               │
      │◀─────────────────────────│                               │
      │                                                          │
      │  🚀 Auto-Redirects to Live Tracking Screen               │
```

### Webhook Verification Code

```python
# Verified against raw binary bytes (never pre-parsed JSON)
raw_body: bytes = await request.body()
received_signature: str = request.headers.get("X-Razorpay-Signature", "")

expected_signature = hmac.new(
    key=settings.razorpay_webhook_secret.encode("utf-8"),
    msg=raw_body,
    digestmod=hashlib.sha256,
).hexdigest()

if not hmac.compare_digest(expected_signature, received_signature):
    raise HTTPException(status_code=401, detail="Invalid webhook signature")
```

- **Reconciliation Worker**: Background worker runs every 60s to poll Razorpay for any orders stuck in `pending_payment` to recover from missed webhooks.
- **Dead Letter Queue (DLQ)**: Failed webhook processing is saved to a persistent dead letter table for inspection and replay.

---

## 📍 Post-Purchase Live Tracking & Delivery Simulator

Once an order is confirmed, MerchantMind transitions into an **active post-purchase delivery concierge** in [`orders/[orderId]/tracking/page.tsx`](file:///Users/utkarshsingh/Desktop/Razorpay_hackathon/frontend/src/app/orders/%5BorderId%5D/tracking/page.tsx):

- **5-Stage Order Progression**: `Order Confirmed` ➔ `Kitchen Preparing` ➔ `Rider Assigned` ➔ `Out for Delivery` ➔ `Delivered`.
- **Haversine Distance & Dynamic ETA**: Calculates distance between the selected Bangalore merchant's GPS coordinates and customer location, factoring in category preparation times (e.g. 20 min bakery prep + 4 min/km road transit).
- **Interactive Voice Querying**: Customers can tap the mic or say *"Where is my food?"* to receive real-time audio progress updates without typing.
- **Web Audio Arrival Chime**: Plays a pleasant harmonic chime when delivery reaches 100% completion.

---

## 💬 Real Conversational Scenarios

### Scenario 1: Cross-Store Discovery with Budget Guardrail
```
User: "I want an eggless chocolate birthday cake under 800 rupees in Indiranagar"
Agent: [DiscoveryAgent ➔ searches 200 Bangalore merchants ➔ parses budget: ₹800.00]
"Found Sweet Bakes Bakery in Indiranagar!
 🎂 Dutch Truffle Eggless Cake (0.5 kg) — ₹650 (Rating: 4.9 ★)
 Remaining budget: ₹150. Would you like me to lock Sweet Bakes Bakery?"
```

### Scenario 2: Contextual Occasion Upselling
```
User: "Yes, lock it and add it to cart"
Agent: [ShoppingAgent ➔ adds cake (₹650) ➔ detects occasion: Birthday]
"Added Dutch Truffle Eggless Cake (₹650) to your cart!
 💡 Since this is for a birthday, would you like to add:
   🕯️ Golden Metallic Birthday Candles — ₹60 (Fits your remaining ₹150 budget!)"

User: "Add the candles and checkout"
Agent: [CheckoutSaga ➔ stock reserved ➔ Razorpay order created]
"Cart Total: ₹710.00 (under your ₹800 budget).
 Here is your Razorpay Payment Link: https://rzp.io/i/mm_ord_8f7b..."
```

---

## 🏆 Forensic Engineering: 16 Production Challenges Solved

Every production engineering challenge encountered and solved during development is documented in [`docs/problems.md`](file:///Users/utkarshsingh/Desktop/Razorpay_hackathon/docs/problems.md):

| # | Challenge Encountered | Root Cause | Engineering Solution | Impact |
|---|---|---|---|---|
| 1 | **ReAct N+1 Query Cascade** | `get_all_merchants_summary` ran 192 queries per turn | Aggregated PostgreSQL `json_agg` query + 5-min TTL cache | Turns dropped from 10.6s to **611ms** |
| 2 | **Razorpay Paise Mismatch** | Float decimals passed to Razorpay API | Strict `int(round(amount * 100))` paise normalization | 100% elimination of `BAD_REQUEST` |
| 3 | **Webhook Signature Failure** | `request.json()` altered raw byte stream before HMAC | Read `await request.body()` directly before JSON parsing | Zero signature falsing |
| 4 | **Unconstrained Upsell Breaches** | Recommender prioritized margin over customer cap | Pre-recommendation `BudgetValidator` constraint | 100% budget compliance |
| 5 | **Inventory Race Conditions** | Standard read-modify-write allowed overselling | Pessimistic `SELECT ... FOR UPDATE` row locks in 2PC saga | Zero stock overselling |
| 6 | **Audio Autoplay Blocks** | Browser security blocked programmatic TTS playback | Hidden AudioContext unlocker primed on first mic tap | Flawless voice playback |
| 7 | **Premature Voice Cutoffs** | 800ms silence timeout cut off conversational pauses | Adaptive 2.2s–3.0s sentence completeness buffer | Natural conversational voice |
| 8 | **Cloud PostgreSQL Scheme Crash** | Railway/Render injected `postgres://` without async dialect | Config sanitizer converting to `postgresql+asyncpg://` | Seamless zero-downtime cloud deploy |
| 9 | **Tracking Redirect Loop** | Sticky `localStorage` key forced chat to tracking on mount | Decoupled active session locks and added `?new=true` | Smooth re-ordering and fresh sessions |
| 10 | **WhatsApp Handshake Rejections** | Meta expected raw plain-text integer for `hub.challenge` | Returned `PlainTextResponse` + Redis message deduplication | Instant Meta verification |

---

## ⚙️ Tech Stack

| Layer | Technology | Specification / Version | Role |
|---|---|---|---|
| **Frontend** | Next.js (App Router) | 16.3 / React 19.2 | Server components, streaming SSR, dynamic routing |
| | Three.js & Tailwind CSS | 0.185 / Tailwind 4.x | 3D particle constellation, glassmorphism UI |
| | Lucide React | 1.34 | Scalable iconography |
| **Backend** | FastAPI | 0.115 (Python 3.12) | High-performance asynchronous API framework |
| | SQLAlchemy & Asyncpg | 2.0 / asyncpg 0.30 | Async ORM, row-level locking, connection pooling |
| | Pydantic | 2.10 | Strict schema validation and type safety |
| | Alembic | 1.14 | Database migrations |
| **AI / Voice** | Groq Cloud API | Llama 3.3 70B & 3.1 8B | Sub-second multi-agent tool calling & reasoning |
| | Deepgram Voice API | Flux Meena / Aura Studio | Low-latency neural speech synthesis (TTS) |
| | Web Speech API | Native SpeechRecognition | Low-latency in-browser speech-to-text (STT) |
| **Payments** | Razorpay SDK | 1.4.2 | Server-side Orders, Payment Links, HMAC Webhooks |
| **Data Layer** | PostgreSQL | 16 | ACID transactions, row-level locking, JSON-LD storage |
| | Redis | 7 | Sliding window rate limits, idempotency, session cache |
| **DevOps** | Docker Compose | Multi-container | Local orchestration (Backend, Postgres, Redis, Nginx) |
| | Netlify | Next.js Runtime | Global edge CDN frontend deployment |

---

## 🚀 Quick Start & Local Development

### Prerequisites
- Docker & Docker Compose
- Python 3.12+
- Node.js 20+

### 1. Clone the Repository
```bash
git clone https://github.com/UtkarshSingh-09/MerchentMind-.git
cd MerchentMind-
```

### 2. Configure Environment
Copy `.env.example` to `.env` and set your credentials:
```bash
cp .env.example .env
```
Key variables:
```ini
GROQ_API_KEY=gsk_...
RAZORPAY_KEY_ID=rzp_test_...
RAZORPAY_KEY_SECRET=...
RAZORPAY_WEBHOOK_SECRET=...
DEEPGRAM_API_KEY=...
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5433/merchantmind
REDIS_URL=redis://localhost:6380/0
```

### 3. Run with Docker Compose
```bash
docker compose up --build
```
- **Web Storefront**: `http://localhost:3000`
- **Backend API**: `http://localhost:8000`
- **Swagger Docs**: `http://localhost:8000/docs`

### 4. Seed the Database
Populate 200 authentic Bangalore stores and 5,000+ items across 20 neighborhoods:
```bash
curl -X POST http://localhost:8000/api/merchants/seed-database
```

---

## 🧪 Testing & Verification Matrix

The test suite contains **151 test cases across 36 specialized test suites**:

```bash
cd backend
pytest tests/ -v --tb=short
```

| Suite | File | What It Formally Verifies |
|---|---|---|
| **Distributed Saga** | `test_saga_compensation.py`, `test_saga_edge_cases.py` | 2PC rollback on payment failure, boundary stock depletion, client tampering overrides |
| **Store Isolation** | `test_single_store_guardrail.py`, `test_multi_tenant.py` | Zero cross-store mixing, tenant data separation, Schema.org catalog export |
| **Adversarial Fuzzing** | `test_prompt_sanitizer_deep_fuzzing.py`, `test_adversarial_jailbreaks.py` | DAN mode, zero-width chars, base64 bypass, key redaction, system prompt leak blocks |
| **Razorpay Payments** | `test_orders.py`, `test_idempotency_precision.py` | Order creation, payment link generation, raw HMAC webhooks, float drift invariance |
| **Security & Limits** | `test_security_hardening.py`, `test_rate_limiter_exhaustive.py` | OWASP headers, payload size caps, sliding-window rate limit, proxy parsing |
| **Spatial & Logistics**| `test_haversine_and_eta.py` | Haversine distance symmetry, prep-time calculation, antipodal coordinate edge cases |
| **Voice & Speech** | `test_voice_service.py` | Deepgram audio streaming, speech synthesis fallbacks, empty query rejection |

---

## 🔄 Enterprise CI/CD Pipeline

MerchantMind implements a multi-stage production CI/CD workflow defined in [`.github/workflows/ci.yml`](file:///.github/workflows/ci.yml) that gates every pull request and push to `main`:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                GITHUB ACTIONS WORKFLOW                                 │
│                                                                                        │
│   [ 1. Security Scan ]       [ 2. Backend CI ]       [ 3. Frontend CI ]   [ 4. Deploy] │
│   ├─ Gitleaks Secrets        ├─ Ruff Lint & Format   ├─ ESLint Checks     └─ Netlify   │
│   ├─ pip-audit (CVEs)        ├─ Live PostgreSQL 16   ├─ TypeScript Check     Edge CDN  │
│   └─ npm audit (Critical)    ├─ Live Redis 7         └─ Next.js 16 Build               │
│                              └─ 151 Pytests + Cov                                      │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

1. **Security & Secret Audit Job**:
   - **Gitleaks v2**: Scans commit history and active diffs for accidental API key or private secret commits.
   - **pip-audit**: Scans Python dependencies against the PyPI Advisory Database for known CVEs.
   - **npm audit**: Fails on any critical vulnerabilities across the frontend dependency graph.
2. **Backend CI Job with Live Service Containers**:
   - Spawns live `postgres:16-alpine` and `redis:7-alpine` Docker service containers inside GitHub Actions runner.
   - Executes **Ruff** for high-speed PEP8 linting and code formatting checks.
   - Runs the full **151-test pytest suite** with `pytest-cov` to enforce test coverage thresholds before merge.
3. **Frontend CI Job**:
   - Runs ESLint validation across Next.js 16 App Router components.
   - Performs strict TypeScript type checking (`tsc --noEmit`) to catch type drifts before compilation.
   - Executes a production build (`npm run build`) to ensure zero SSR hydration or bundle errors.
4. **Continuous Edge Deployment**:
   - Passes clean artifacts to Netlify Edge CDN for instant automatic preview and production deployments.

---

## ⚡ Scalability, Concurrency & Load Testing

MerchantMind is engineered to handle high-concurrency flash sales, unbatched multi-agent queries, and burst checkouts without deadlocks or stock overselling.

### k6 Performance & Stress Testing Suite

The system includes a production load test harness in [`load_test.js`](file:///load_test.js) simulating realistic customer behavior:

```bash
# Execute 300 VU sustained load + 50 VU burst checkout stress test
k6 run load_test.js
```

| Scenario | Virtual Users (VUs) | Duration | Load Pattern | Target Threshold |
|---|:---:|:---:|---|---|
| **Sustained Chat & Discovery** | **300 VUs** | 5 minutes | Ramp from 10 ➔ 300 VUs exploring catalogs & reasoning | `p(95) < 800ms` (non-LLM) |
| **Burst Checkout Stress** | **50 Concurrent VUs** | 1 minute | Concurrent checkout requests against constrained stock units | `error_rate < 1.0%` |
| **End-to-End Latency Target** | — | — | Overall system p95 across all endpoints | `p(95) < 2500ms` |

### Architectural Scalability Levers

1. **Pessimistic Concurrency & Stock Locks**:
   - Checkout uses `SELECT ... FOR UPDATE` inside SQLAlchemy async sessions. Competing transactions wait for lock release rather than reading stale dirty state, completely eliminating race conditions and negative inventory drift.
2. **N+1 Catalog Query Elimination (10.6s ➔ 611ms)**:
   - Replaced 192 separate SQL queries across merchants, categories, and items with a single aggregated PostgreSQL `json_agg` query backed by an in-memory 5-minute TTL cache.
3. **Asynchronous Connection Pooling**:
   - **Database**: PostgreSQL engine configured with `asyncpg` connection pool (`pool_size=20`, `max_overflow=10`).
   - **Voice Engine**: Persistent HTTP/2 connection pooling with `httpx.Limits(max_keepalive_connections=20, max_connections=50)` eliminating TCP/TLS handshake latency on voice turns.
4. **Redis Sliding-Window Rate Limiting**:
   - Distributed sliding-window counter tracking client requests per minute (`100 req/min`), with multi-hop `X-Forwarded-For` proxy parsing for accurate IP isolation.
5. **Circuit Breaker & Fallback**:
   - Wraps Groq LLM inference with an automatic circuit breaker that fails over from Llama 3.3 70B to Llama 3.1 8B with exponential backoff on transient upstream timeouts.

---

## 📡 API Reference

### Conversational Commerce & AI
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/chat/` | Send conversational message (returns rich product recommendations & cart) |
| `POST` | `/api/chat/stream` | Real-time SSE streaming endpoint with agent reasoning transparency |
| `GET` | `/api/voice/status` | Verify Deepgram Voice AI connectivity and model availability |
| `POST` | `/api/voice/speak` | Synthesize ultra-low latency audio using Deepgram Flux Meena |

### Razorpay Orders & Checkout
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/orders/` | Execute checkout saga, reserve stock, and generate Razorpay Payment Link |
| `GET` | `/api/orders/{id}` | Fetch order details, line items, and fulfillment information |
| `GET` | `/api/orders/{id}/status` | Poll payment confirmation status |
| `GET` | `/api/orders/{id}/tracking` | Fetch real-time delivery coordinates, rider ETA, and Haversine distance |
| `GET` | `/api/orders/{id}/audit` | Fetch complete immutable chronological audit trail |

### Webhooks & Integrations
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/webhooks/razorpay` | Cryptographically verified HMAC-SHA256 Razorpay payment webhook |
| `POST` | `/api/webhooks/telegram` | Telegram Bot update and payment callback handler |
| `GET/POST`| `/api/webhooks/whatsapp` | Meta WhatsApp Cloud API handshake verification and message receiver |

### Merchant Operations & Catalog
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/merchants/` | List all registered merchants with ratings and coordinates |
| `POST` | `/api/merchants/seed-database`| Instant seeding of 200 authentic Bangalore stores and 5,000+ items |
| `GET` | `/api/merchants/{id}/catalog.json` | Schema.org JSON-LD AI-readable catalog export |
| `GET` | `/api/analytics/dashboard` | Merchant business intelligence: revenue, AOV, funnel conversions |

---

## 🌍 Deployment

- **Frontend**: Live on **Netlify Edge CDN** at [merchantmind-ai.netlify.app](https://merchantmind-ai.netlify.app)
- **Backend**: Containerized FastAPI service with PostgreSQL 16 & Redis 7
- **CI/CD Pipeline**: Automated GitHub Actions running full test suite on push

---

## 📄 License

This project is open-source under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

<div align="center">

**Built with ❤️ for the Razorpay AI Buildathon 2026**

[⬆ Back to Top](#-merchantmind)

</div>
