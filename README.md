<div align="center">

# 🧠 MerchantMind

**`Autonomous AI Shopping & Growth Agent for Razorpay Merchants`**

<br/>

[![Python](https://img.shields.io/badge/Python-3.12-D97706?style=for-the-badge&logo=python&logoColor=white&labelColor=151515)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-991B1B?style=for-the-badge&logo=fastapi&logoColor=white&labelColor=151515)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-16-FBBF24?style=for-the-badge&logo=next.js&logoColor=white&labelColor=151515)](https://nextjs.org)
[![React](https://img.shields.io/badge/React-19-61DAFB?style=for-the-badge&logo=react&logoColor=white&labelColor=151515)](https://react.dev)
[![Groq](https://img.shields.io/badge/Groq-Llama_3.3_70B-D97706?style=for-the-badge&labelColor=151515)](https://groq.com)
[![Razorpay](https://img.shields.io/badge/Razorpay-Payment_Links-2962FF?style=for-the-badge&logo=razorpay&logoColor=white&labelColor=151515)](https://razorpay.com)
[![Telegram](https://img.shields.io/badge/Telegram-Bot_API-26A5E4?style=for-the-badge&logo=telegram&logoColor=white&labelColor=151515)](https://core.telegram.org/bots)
[![License](https://img.shields.io/badge/License-MIT-FBBF24?style=for-the-badge&labelColor=151515)](LICENSE)

<br/>

**Track 01 · AI Growth & Agentic Commerce · Razorpay AI Buildathon 2026**

[🌐 Live Demo](https://merchantmind-ai.netlify.app) · [📖 Architecture](ARCHITECTURE.md) · [🐛 Report Bug](https://github.com/UtkarshSingh-09/MerchentMind-/issues) · [💡 Request Feature](https://github.com/UtkarshSingh-09/MerchentMind-/issues)

---

</div>

## 📋 Table of Contents

- [The Problem](#-the-problem)
- [The Solution](#-the-solution)
- [Architecture](#-architecture)
- [Multi-Agent Intelligence](#-multi-agent-intelligence)
- [Razorpay Integration Deep Dive](#-razorpay-integration-deep-dive)
- [Core Features](#-core-features)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Try It Live](#-try-it-live)
- [API Reference](#-api-reference)
- [Testing](#-testing)
- [Deployment](#-deployment)
- [License](#-license)

---

## 🔴 The Problem

Traditional e-commerce storefronts are **static, menu-driven, and passive**. Customers browse, scroll, abandon.

| Pain Point | Impact |
|---|---|
| **Choice Overload** | 214 stores × 50+ items each = paralysis. Customers leave before buying. |
| **Zero Upselling Intelligence** | Static menus can't suggest birthday candles when someone buys a cake. Merchants lose 15–30% potential AOV. |
| **Fragmented Payment UX** | Copy-paste UPI IDs, manual bank transfers, no real-time confirmation — high drop-off at checkout. |
| **No Omnichannel Reach** | Customers are on Telegram, WhatsApp, and web. Merchants are stuck on one. |
| **Manual Reactivation** | Dormant customers get no targeted campaigns. Zero retention automation. |

> **The bottom line:** Small merchants lose revenue because they can't offer the *intelligent, personalized, instant-checkout* experience that customers expect in 2026.

---

## 🟢 The Solution

**MerchantMind** transforms static product catalogs into **autonomous, AI-powered commerce engines** — a shopping agent that *thinks, recommends, upsells, and closes deals* on behalf of the merchant.

```
   "I want a chocolate cake           ┌─────────────────────────────┐
    under ₹500 for a birthday"  ──▶  │     🧠 MerchantMind Agent   │
                                      │                             │
                                      │  1. Understands intent      │
                                      │  2. Searches 214 stores     │
                                      │  3. Recommends best fit     │
                                      │  4. Suggests candles 🕯️     │
                                      │  5. Guards your budget      │
                                      │  6. Generates Razorpay link │
                                      │  7. Confirms payment ✅     │
                                      └─────────────────────────────┘
```

**One natural language message. Full checkout. Zero friction.**

---

## 🏗️ Architecture

### High-Level System Topology

```
┌──────────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                                  │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐  │
│   │  Next.js 16  │  │  Telegram    │  │  Ambient Voice Engine    │  │
│   │  Web Chat UI │  │  Bot API     │  │  (Web Speech API + STT)  │  │
│   └──────┬───────┘  └──────┬───────┘  └────────────┬─────────────┘  │
└──────────┼─────────────────┼───────────────────────┼────────────────┘
           │                 │                       │
           ▼                 ▼                       ▼
┌──────────────────────────────────────────────────────────────────────┐
│                     API GATEWAY (Nginx)                              │
└──────────────────────────────┬───────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────────┐
│                   APPLICATION LAYER (FastAPI + Uvicorn)              │
│                                                                      │
│   ┌──────────────────────────────────────────────────────────────┐   │
│   │              MULTI-AGENT ORCHESTRATOR                        │   │
│   │   ┌──────────────┐  ┌───────────────┐  ┌────────────────┐   │   │
│   │   │ AgentRouter  │─▶│ DiscoveryAgent│  │ MerchantAgent  │   │   │
│   │   │ (Intent      │  │ (Cross-store  │  │ (Store-level   │   │   │
│   │   │  Classifier) │  │  search)      │  │  analytics)    │   │   │
│   │   └──────────────┘  └───────────────┘  └────────────────┘   │   │
│   │          │           ┌───────────────┐  ┌────────────────┐   │   │
│   │          └──────────▶│ ShoppingAgent │─▶│ CheckoutSaga   │   │   │
│   │                      │ (Cart + LLM   │  │ (2PC Razorpay  │   │   │
│   │                      │  Upsell)      │  │  Orchestrator) │   │   │
│   │                      └───────────────┘  └────────────────┘   │   │
│   └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
│   ┌────────────────┐  ┌────────────────┐  ┌──────────────────────┐  │
│   │ Budget Guard   │  │ Prompt Sanitiz │  │ Circuit Breaker      │  │
│   │ (Hard ₹ cap)   │  │ (Jailbreak     │  │ (Groq failover)      │  │
│   │                │  │  protection)   │  │                      │  │
│   └────────────────┘  └────────────────┘  └──────────────────────┘  │
└──────────────────────────────┬───────────────────────────────────────┘
                               │
           ┌───────────────────┼───────────────────┐
           ▼                   ▼                   ▼
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────────────┐
│  Groq Cloud API  │ │   Razorpay API   │ │     Data Layer           │
│  Llama 3.3 70B   │ │  Orders + Links  │ │  PostgreSQL 16 (ACID)    │
│  Llama 3.1 8B    │ │  Webhooks (HMAC) │ │  Redis 7 (Sessions)      │
│  (fallback)      │ │  Checkout.js     │ │                          │
└──────────────────┘ └──────────────────┘ └──────────────────────────┘
```

### End-to-End Request Lifecycle

```
Customer Message ──▶ SSE Stream ──▶ AgentRouter (intent classification)
                                         │
                          ┌──────────────┴──────────────┐
                          ▼                              ▼
                   DiscoveryAgent                  ShoppingAgent
                   (no merchant locked)            (merchant locked)
                          │                              │
                          ▼                              ▼
                   Groq ReAct Loop               Cart Management
                   search_all_merchants()        add/remove/clear
                          │                              │
                          ▼                              ▼
                   Budget-Bounded              Context-Aware Upsell
                   Recommendations             (occasion detection)
                                                         │
                                                         ▼
                                                  CheckoutSaga (2PC)
                                                  ├─ Phase 1: Stock Lock
                                                  ├─ Phase 2: Razorpay Order
                                                  └─ Phase 3: Payment Link
                                                         │
                                                         ▼
                                                  Webhook Capture ──▶ PAID ✅
```

---

## 🤖 Multi-Agent Intelligence

MerchantMind doesn't use a single monolithic LLM call. It deploys a **fleet of specialized agents**, each with its own tools, system prompts, and guardrails.

### Agent Architecture

| Agent | Model | Role | Tools |
|---|---|---|---|
| **AgentRouter** | Llama 3.1 8B | Classifies user intent and routes to the correct specialist agent | `classify_routing_intent()` |
| **DiscoveryAgent** | Llama 3.3 70B | Cross-store product discovery and comparison across 214 merchants | `search_all_merchants()`, `get_merchant_info()`, `search_merchant_products()` |
| **ShoppingAgent** | Llama 3.3 70B | In-store shopping with cart management, upselling, and checkout | `add_to_cart()`, `remove_from_cart()`, `get_cart()`, `execute_checkout()` |
| **MerchantAgent** | Llama 3.3 70B | Store-level analytics, inventory insights, and campaign management | `get_store_analytics()`, `dispatch_campaign()` |
| **CheckoutSaga** | — (deterministic) | Two-phase commit orchestrator for Razorpay payment lifecycle | Razorpay SDK direct calls |

### Intelligence Pipeline

```
┌──────────────────────────────────────────────────────────────────┐
│                    INTELLIGENCE PIPELINE                         │
│                                                                  │
│  User Message                                                    │
│       │                                                          │
│       ▼                                                          │
│  ┌─────────────────┐    ┌──────────────────┐                    │
│  │ Prompt Sanitizer │───▶│ Budget Extractor  │                    │
│  │ (Jailbreak       │    │ (NLP ₹ parsing)   │                    │
│  │  detection)       │    └────────┬─────────┘                    │
│  └─────────────────┘             │                               │
│                                  ▼                               │
│                    ┌──────────────────────┐                      │
│                    │   Entity Resolver     │                      │
│                    │  (Fuzzy name match    │                      │
│                    │   across catalogs)    │                      │
│                    └──────────┬───────────┘                      │
│                               │                                  │
│                               ▼                                  │
│                    ┌──────────────────────┐                      │
│                    │   ReAct Tool Loop     │                      │
│                    │  (Groq function       │                      │
│                    │   calling, multi-     │                      │
│                    │   turn reasoning)     │                      │
│                    └──────────┬───────────┘                      │
│                               │                                  │
│                               ▼                                  │
│                    ┌──────────────────────┐                      │
│                    │   Upsell Engine       │                      │
│                    │  (Occasion pairing    │                      │
│                    │   + remaining budget  │                      │
│                    │   computation)        │                      │
│                    └──────────────────────┘                      │
└──────────────────────────────────────────────────────────────────┘
```

### Guardrails & Safety

- **Hard Budget Enforcement** — `cart_total > stated_budget` blocks payment link creation with a `BUDGET_VIOLATION` event
- **Prompt Injection Defense** — Multi-layer sanitizer catches jailbreak attempts before they reach the LLM
- **Circuit Breaker** — Automatic failover from Llama 3.3 70B → Llama 3.1 8B with exponential backoff on Groq transient failures
- **Rate Limiting** — Redis-backed sliding window rate limiter per IP/session
- **Idempotency** — Webhook deduplication prevents double-processing of Razorpay events

---

## 💳 Razorpay Integration Deep Dive

MerchantMind is built **natively** on Razorpay's payment infrastructure — not a thin wrapper, but a deep integration across the full payment lifecycle.

### Payment Flow

```
┌────────────┐     ┌──────────────┐     ┌──────────────────────┐
│  Customer   │     │ MerchantMind │     │     Razorpay API     │
│  (Browser)  │     │   Backend    │     │                      │
└──────┬─────┘     └──────┬───────┘     └──────────┬───────────┘
       │                  │                         │
       │  "Checkout"      │                         │
       │─────────────────▶│                         │
       │                  │  POST /v1/orders        │
       │                  │────────────────────────▶│
       │                  │                         │
       │                  │  order_id               │
       │                  │◀────────────────────────│
       │                  │                         │
       │                  │  POST /v1/payment_links │
       │                  │────────────────────────▶│
       │                  │                         │
       │                  │  short_url              │
       │                  │◀────────────────────────│
       │                  │                         │
       │  Payment Link    │                         │
       │◀─────────────────│                         │
       │                  │                         │
       │  Opens Razorpay Standard Checkout          │
       │───────────────────────────────────────────▶│
       │                  │                         │
       │  UPI / Card / Netbanking                   │
       │───────────────────────────────────────────▶│
       │                  │                         │
       │                  │  Webhook: payment.captured
       │                  │◀────────────────────────│
       │                  │  HMAC-SHA256 verified ✅ │
       │                  │                         │
       │                  │  Update DB → PAID       │
       │  Poll status     │                         │
       │─────────────────▶│                         │
       │  status: "paid"  │                         │
       │◀─────────────────│                         │
       │                  │                         │
       │  🎉 Order Confirmed                        │
```

### Razorpay APIs Used

| API | Purpose | Security |
|---|---|---|
| **Orders API** (`/v1/orders`) | Create server-side order with amount, currency, receipt | Basic Auth (key_id:key_secret) |
| **Payment Links API** (`/v1/payment_links`) | Generate short URLs for instant payment collection | Basic Auth + callback_url |
| **Webhooks** (`payment.captured`, `payment_link.paid`) | Real-time payment status notifications | HMAC-SHA256 signature verification |
| **Checkout.js** (Standard) | Embedded payment modal in the web UI | Auto-loaded via payment link |

### Webhook Security

```python
# HMAC-SHA256 Verification (every incoming webhook)
expected_signature = hmac.new(
    key=RAZORPAY_WEBHOOK_SECRET.encode(),
    msg=request_body,
    digestmod=hashlib.sha256
).hexdigest()

if not hmac.compare_digest(expected_signature, received_signature):
    raise HTTPException(401, "Invalid webhook signature")
```

- **Dead Letter Queue** — Failed webhook processing is retried via DLQ, never silently dropped
- **Reconciliation Daemon** — Background worker runs every 60s to catch any missed webhooks by polling Razorpay order status directly
- **Immutable Audit Trail** — Every payment event is logged to PostgreSQL with full request body, timestamp, and verification status

---

## ✨ Core Features

### 🛒 Conversational Checkout
Natural language shopping — understands intent, flavors, occasions, quantities, and price constraints. *"I need a dark chocolate birthday cake under ₹800"* → instant results with reasoning.

### 📈 Context-Aware Upselling
Proactive occasion detection (Cake → Birthday Candles + Balloon Combo). Budget-bounded — computes `remaining_budget = stated_budget - cart_total` and never overshoots.

### 📱 Omnichannel Commerce
Same agent brain, three frontends:
- **Web Chat** — Next.js 16 with glassmorphism UI, voice input, animated product cards
- **Telegram Bot** — Inline keyboard buttons, instant Razorpay pay links in-chat
- **Voice** — Ambient voice engine via Web Speech API for hands-free ordering

### 🔍 AI-Readable Catalog (Schema.org)
`GET /api/merchants/{id}/catalog.json` exports catalogs in Schema.org `ItemList` + `Product` + `Offer` JSON-LD format — discoverable by autonomous AI agents and search engines.

### 📊 Merchant Analytics Dashboard
Revenue breakdown, order funnel, customer cohorts, AOV trends — all powered by real transaction data from the Razorpay integration.

### 🛡️ Production-Grade Resilience
Circuit breaker, rate limiter, DLQ, reconciliation daemon, idempotency keys, prompt sanitization, HMAC verification.

---

## ⚙️ Tech Stack

| Layer | Technology | Version | Purpose |
|---|---|---|---|
| **Frontend** | Next.js (App Router) | 16.3 | Server components, streaming SSR |
| | React | 19.2 | UI rendering with concurrent features |
| | Tailwind CSS | 4.x | Utility-first styling |
| | Framer Motion | 13.x | Micro-animations and transitions |
| | Three.js | 0.185 | 3D particle effects (landing page) |
| | Lucide React | 1.34 | Icon system |
| **Backend** | FastAPI | 0.115 | Async API framework (Uvicorn ASGI) |
| | SQLAlchemy | 2.0 | Async ORM with asyncpg driver |
| | Pydantic | 2.x | Request/response validation |
| | Alembic | 1.14 | Database migrations |
| **AI / LLM** | Groq API | — | Ultra-fast inference (< 200ms TTFT) |
| | Llama 3.3 70B | Primary | Complex reasoning, tool calling |
| | Llama 3.1 8B | Fallback | Lightweight routing, classification |
| **Payments** | Razorpay SDK | 1.4.2 | Orders, Payment Links, Webhooks |
| **Messaging** | Telegram Bot API | — | Interactive keyboards, pay buttons |
| **Data** | PostgreSQL | 16 | ACID-compliant relational + JSONB |
| | Redis | 7 | Session cache, rate limits, circuit state |
| **Infra** | Docker Compose | — | Multi-container orchestration |
| | Nginx | Alpine | Reverse proxy, load balancing |
| | GitHub Actions | — | CI/CD pipeline |
| | Netlify | — | Frontend CDN deployment |

---

## 📁 Project Structure

```
MerchantMind/
├── backend/
│   ├── app/
│   │   ├── agents/                    # Multi-agent intelligence layer
│   │   │   ├── agent_router.py        #   Intent classifier & agent dispatcher
│   │   │   ├── discovery_agent.py     #   Cross-store product discovery (161KB)
│   │   │   ├── shopping_agent.py      #   In-store cart + upsell agent (89KB)
│   │   │   ├── checkout_agent.py      #   Razorpay checkout orchestrator
│   │   │   └── merchant_agent.py      #   Store analytics & campaigns
│   │   ├── services/                  # Business logic & external integrations
│   │   │   ├── razorpay_service.py    #   Razorpay Orders + Payment Links
│   │   │   ├── checkout_saga.py       #   Two-phase commit payment flow
│   │   │   ├── catalog_search.py      #   Semantic product search engine
│   │   │   ├── upsell_engine.py       #   Occasion-aware upselling rules
│   │   │   ├── budget_extractor.py    #   NLP budget parsing from messages
│   │   │   ├── entity_resolver.py     #   Fuzzy entity name matching
│   │   │   ├── groq_client.py         #   LLM client with circuit breaker
│   │   │   ├── circuit_breaker.py     #   Fault-tolerant Groq failover
│   │   │   ├── prompt_sanitizer.py    #   Jailbreak & injection defense
│   │   │   ├── audit_service.py       #   Immutable decision audit log
│   │   │   ├── campaign_service.py    #   Dormant customer reactivation
│   │   │   ├── memory_service.py      #   Conversation memory management
│   │   │   ├── telegram_service.py    #   Telegram Bot API integration
│   │   │   ├── whatsapp_service.py    #   WhatsApp Business API
│   │   │   ├── reconciliation_service.py  # Missed webhook recovery
│   │   │   ├── idempotency_service.py #   Webhook deduplication
│   │   │   └── dlq_service.py         #   Dead letter queue for failures
│   │   ├── routes/                    # API endpoints
│   │   │   ├── chat.py                #   POST /api/chat/ (SSE streaming)
│   │   │   ├── orders.py              #   Order CRUD + status polling
│   │   │   ├── webhooks.py            #   Razorpay + Telegram + WhatsApp
│   │   │   ├── merchants.py           #   Merchant catalog & info
│   │   │   ├── analytics.py           #   Revenue & funnel analytics
│   │   │   ├── campaigns.py           #   AI campaign dispatch
│   │   │   └── voice.py               #   Voice transcription endpoint
│   │   ├── models/                    # SQLAlchemy ORM models
│   │   ├── schemas/                   # Pydantic request/response schemas
│   │   ├── middleware/                # CORS, auth, rate limiting
│   │   ├── config.py                  # Environment & settings
│   │   ├── database.py                # Async engine + session factory
│   │   └── main.py                    # FastAPI app entry point
│   ├── tests/                         # 36 test files, 151+ test cases
│   ├── alembic/                       # Database migrations
│   ├── scripts/                       # Seed data & utilities
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx               # Landing page (3D particles + CTA)
│   │   │   ├── chat/page.tsx          # Main conversational checkout UI
│   │   │   ├── orders/[orderId]/      # Dynamic order pages
│   │   │   ├── tracking/             # Live order tracking
│   │   │   ├── analytics/            # Merchant analytics dashboard
│   │   │   ├── architecture/         # System architecture visualizer
│   │   │   ├── intelligence/         # AI agent showcase
│   │   │   └── merchant/             # Merchant management portal
│   │   ├── components/
│   │   │   ├── ChatMessage.tsx        # Rich message renderer (markdown + cards)
│   │   │   ├── CartSidebar.tsx        # Slide-out cart with live totals
│   │   │   ├── ProductCard.tsx        # Animated product display cards
│   │   │   ├── VoiceOrb.tsx           # Ambient voice input visualizer
│   │   │   ├── AgentReasoningPanel.tsx # Live AI reasoning transparency
│   │   │   ├── PresentationModal.tsx  # Embedded slide deck viewer
│   │   │   └── ParticleConstellation.tsx  # 3D background effects
│   │   └── lib/                       # Shared utilities
│   ├── public/                        # Static assets
│   ├── package.json
│   └── Dockerfile
│
├── nginx/
│   └── nginx.conf                     # Reverse proxy configuration
├── docker-compose.yml                 # Full-stack orchestration
├── .env.example                       # Environment variable template
├── .github/workflows/                 # CI/CD pipeline
├── ARCHITECTURE.md                    # Detailed system architecture (49KB)
├── netlify.toml                       # Frontend deployment config
└── LICENSE                            # MIT License
```

---

## 🚀 Try It Live

> **🌐 [merchantmind-ai.netlify.app](https://merchantmind-ai.netlify.app)** — Open the live demo and start shopping with the AI agent instantly. No setup required.

---

## 📡 API Reference

### Chat & AI

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/chat/` | Send message to AI agent (SSE streaming response) |
| `POST` | `/api/chat/stream` | Real-time SSE stream with thinking + tool calls |
| `POST` | `/api/voice/transcribe` | Voice audio → text transcription |

### Orders & Payments

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/orders/` | Create order + generate Razorpay Payment Link |
| `GET` | `/api/orders/{id}/status` | Poll payment confirmation status |
| `GET` | `/api/orders/{id}/audit` | Full chronological audit trail |

### Webhooks

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/webhooks/razorpay` | HMAC-SHA256 verified payment webhooks |
| `POST` | `/api/webhooks/telegram` | Telegram Bot update handler |
| `GET/POST` | `/api/webhooks/whatsapp` | Meta WhatsApp verification + messages |

### Merchants & Catalog

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/merchants/` | List all merchants |
| `GET` | `/api/merchants/{id}` | Merchant details + products |
| `GET` | `/api/merchants/{id}/catalog.json` | Schema.org / JSON-LD AI-readable catalog |

### Analytics & Campaigns

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/analytics/dashboard` | Revenue, orders, AOV, funnel metrics |
| `POST` | `/api/campaigns/dispatch` | AI-powered dormant customer reactivation |

---

## 🧪 Testing

### Test Suite: 36 Files · 151+ Test Cases

```bash
cd backend
pytest tests/ -v --tb=short
```

### Test Coverage Breakdown

| Category | Test Files | What's Tested |
|---|---|---|
| **Core Flow** | `test_orders.py`, `test_chat.py` | Full order lifecycle, SSE streaming |
| **AI Agents** | `test_upsell.py`, `test_single_store_guardrail.py` | Upsell accuracy, store-lock enforcement |
| **Security** | `test_adversarial_jailbreaks.py`, `test_security_hardening.py` | Prompt injection, auth bypass, RBAC |
| **Payments** | `test_saga_compensation.py`, `test_saga_edge_cases.py` | 2PC rollback, double-pay prevention |
| **Resilience** | `test_circuit_breaker.py`, `test_dlq_and_webhook_resilience.py` | Failover, dead letter recovery |
| **Data** | `test_multi_tenant.py`, `test_concurrency_race.py` | Tenant isolation, race condition safety |
| **Integrations** | `test_telegram.py`, `test_whatsapp.py` | Bot message handling, webhook verify |
| **NLP** | `test_budget_extractor_comprehensive.py`, `test_entity_resolver_fuzzing.py` | ₹ parsing, fuzzy matching accuracy |

---

## 🌍 Deployment

### Live Demo

The frontend is deployed on **Netlify** with automatic deploys from the `main` branch:

🌐 **[merchantmind-ai.netlify.app](https://merchantmind-ai.netlify.app)**

### Production Architecture

```
GitHub Push → GitHub Actions CI → Tests Pass → Netlify Build → CDN Deploy
                                                    │
                                              Backend (VPS)
                                              ├── Docker Compose
                                              ├── PostgreSQL 16
                                              ├── Redis 7
                                              └── Nginx SSL Termination
```

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

<div align="center">

**Built with ❤️ for the Razorpay AI Buildathon 2026**

[⬆ Back to Top](#-merchantmind)

</div>
